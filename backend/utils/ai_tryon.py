"""
AI 虚拟试穿工具 - DashScope OutfitAnyone (AI试衣)

使用阿里云百炼的 aitryon 专用虚拟试穿模型:
  - 输入: 模特全身照 + 衣物平拍图
  - 输出: 模特穿着该衣物的合成效果图
  - 保留模特面部特征，衣物颜色/纹理/版型与参考图一致

流程:
  1. 上传图片到 DashScope 获取 oss:// 临时 URL
  2. 调用 aitryon API (异步)
  3. 轮询获取结果
"""
import base64
import io
import json
import time
import asyncio
import os
import uuid
import logging
from typing import Optional

import httpx
from PIL import Image

from config import get_settings

logger = logging.getLogger("ai_tryon")
# 确保日志输出到控制台
import sys as _sys
if not logger.handlers:
    _handler = logging.StreamHandler(_sys.stdout)
    _handler.setFormatter(logging.Formatter("[ai_tryon] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.DEBUG)

# 上装/下装分类
TOP_CATEGORIES = {"short_sleeve", "long_sleeve", "hoodie", "coat", "dress", "accessories"}
BOTTOM_CATEGORIES = {"pants", "shorts", "shoes", "sneakers"}


# ============================================================
# 图片预处理
# ============================================================

def _resize_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """缩放图片，最长边不超过max_size"""
    logger.debug(f"_resize_image: input {len(image_bytes)} bytes")
    img = Image.open(io.BytesIO(image_bytes))
    logger.debug(f"_resize_image: opened {img.size}, mode={img.mode}, format={img.format}")
    # 确保RGB模式
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        logger.debug(f"_resize_image: resized to {img.size}")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    result = buf.getvalue()
    logger.debug(f"_resize_image: output {len(result)} bytes")
    return result


# ============================================================
# DashScope 文件上传 → oss:// URL
# ============================================================

async def _upload_to_dashscope(image_bytes: bytes, filename: str = "image.jpg") -> Optional[str]:
    """
    上传图片到 DashScope，获取 oss:// 临时 URL
    步骤:
      1. GET /api/v1/uploads?action=getPolicy 获取上传凭证
      2. POST 到 OSS 上传文件
      3. 返回 oss://{key}
    """
    settings = get_settings()
    api_key = settings.dashscope_api_key

    try:
        # Step 1: 获取上传策略
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://dashscope.aliyuncs.com/api/v1/uploads",
                params={"action": "getPolicy", "model": "aitryon"},
                headers={"Authorization": f"Bearer {api_key}"},
            )

        policy_data = resp.json()
        if "data" not in policy_data:
            logger.error(f"Get upload policy failed: {json.dumps(policy_data, ensure_ascii=False)[:300]}")
            return None

        data = policy_data["data"]
        upload_host = data.get("upload_host", "") or data.get("host", "")
        upload_dir = data.get("upload_dir", "") or data.get("dir", "")
        policy = data.get("policy", "")
        signature = data.get("signature", "")
        access_id = data.get("oss_access_key_id", "")
        if not access_id:
            access_id = data.get("OSSAccessKeyId", "")

        # 确保 upload_host 有协议前缀
        if upload_host and not upload_host.startswith("http"):
            upload_host = "https://" + upload_host

        # 构建文件key
        file_key = f"{upload_dir}/{uuid.uuid4().hex}_{filename}"

        # Step 2: 上传文件到 OSS
        form_data = {
            "key": file_key,
            "policy": policy,
            "OSSAccessKeyId": access_id,
            "signature": signature,
            "x-oss-object-acl": data.get("x_oss_object_acl", "private"),
            "x-oss-forbid-overwrite": data.get("x_oss_forbid_overwrite", data.get("x_oss_forbidden_overwrite", "true")),
            "success_action_status": "200",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                upload_host,
                data=form_data,
                files={"file": (filename, io.BytesIO(image_bytes), "image/jpeg")},
            )

        if resp.status_code in (200, 204):
            oss_url = f"oss://{file_key}"
            logger.info(f"Uploaded to DashScope: {oss_url}")
            return oss_url
        else:
            logger.error(f"OSS upload failed: HTTP {resp.status_code}, body: {resp.text[:200]}")
            return None

    except Exception as e:
        logger.error(f"Upload to DashScope exception: {e}")
        return None


# ============================================================
# DashScope aitryon 虚拟试穿
# ============================================================

async def _call_aitryon(
    person_oss_url: str,
    top_garment_oss_url: Optional[str] = None,
    bottom_garment_oss_url: Optional[str] = None,
) -> Optional[dict]:
    """
    调用 DashScope aitryon 虚拟试穿 API
    返回: {"success": bool, "imageUrl": str, "message": str}
    """
    settings = get_settings()
    api_key = settings.dashscope_api_key

    input_data = {
        "person_image_url": person_oss_url,
    }
    if top_garment_oss_url:
        input_data["top_garment_url"] = top_garment_oss_url
    if bottom_garment_oss_url:
        input_data["bottom_garment_url"] = bottom_garment_oss_url

    payload = {
        "model": "aitryon",
        "input": input_data,
        "parameters": {
            "resolution": -1,
            "restore_face": True,
        },
    }

    logger.info(f"Calling aitryon API: person={person_oss_url}, top={top_garment_oss_url}, bottom={bottom_garment_oss_url}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
        "X-DashScope-OssResourceResolve": "enable",
    }

    try:
        # 提交异步任务
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis",
                headers=headers,
                json=payload,
            )

        data = resp.json()
        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            logger.error(f"aitryon submit failed: {json.dumps(data, ensure_ascii=False)[:300]}")
            msg = data.get("message", "aitryon API提交失败")
            return {"success": False, "imageUrl": None, "message": msg}

        logger.info(f"aitryon task submitted: {task_id}")

        # 轮询结果
        return await _poll_aitryon_result(task_id, api_key)

    except Exception as e:
        logger.error(f"aitryon API exception: {e}")
        return {"success": False, "imageUrl": None, "message": f"aitryon API异常: {str(e)}"}


async def _poll_aitryon_result(task_id: str, api_key: str, timeout: int = 180) -> Optional[dict]:
    """轮询 aitryon 任务结果"""
    start = time.time()

    while time.time() - start < timeout:
        await asyncio.sleep(3)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            result = resp.json()
            status = result.get("output", {}).get("task_status", "")

            if status == "SUCCEEDED":
                # aitryon 返回 image_url 字段
                image_url = result.get("output", {}).get("image_url")
                # 兼容: 也检查 results 数组
                if not image_url:
                    results = result.get("output", {}).get("results", [])
                    if results:
                        image_url = results[0].get("url")
                if image_url:
                    # 下载图片保存到本地
                    local_url = await _download_and_save(image_url)
                    if local_url:
                        return {"success": True, "imageUrl": local_url, "message": "AI试穿生成成功"}
                    return {"success": True, "imageUrl": image_url, "message": "AI试穿生成成功"}
                logger.warning(f"aitryon SUCCEEDED but no image_url found: {json.dumps(result, ensure_ascii=False)[:500]}")
                return {"success": False, "imageUrl": None, "message": "生成完成但未获取到图片"}

            elif status == "FAILED":
                msg = result.get("output", {}).get("message", "AI试穿生成失败")
                logger.error(f"aitryon task failed: {msg}")
                return {"success": False, "imageUrl": None, "message": msg}

            else:
                logger.debug(f"aitryon polling... status={status}")

        except Exception as e:
            logger.error(f"Poll exception: {e}")
            continue

    return {"success": False, "imageUrl": None, "message": "AI试穿生成超时，请稍后重试"}


async def _download_and_save(url: str) -> Optional[str]:
    """下载远程图片并保存到本地 uploads 目录"""
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
        if resp.status_code == 200:
            filename = f"tryon_{uuid.uuid4().hex[:12]}.jpg"
            filepath = os.path.join(settings.upload_dir, filename)
            os.makedirs(settings.upload_dir, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return f"/uploads/{filename}"
    except Exception as e:
        logger.error(f"Download image failed: {e}")
    return None


# ============================================================
# 主入口
# ============================================================

async def generate_tryon(
    model_image_bytes: bytes,
    clothing_images: list[bytes],
    clothing_items: list[dict],
    gender: str = "female",
) -> dict:
    """
    虚拟试穿主入口 - 使用 DashScope aitryon 专用试穿模型

    流程:
      1. 将模特图上传到 DashScope → oss:// URL
      2. 将衣物图上传到 DashScope → oss:// URL (区分上装/下装)
      3. 调用 aitryon API 生成试穿效果图
      4. 轮询获取结果并保存到本地
    """
    settings = get_settings()

    if not settings.dashscope_api_key:
        return {"success": False, "imageUrl": None, "message": "DashScope API密钥未配置"}

    # 预处理图片
    logger.info(f"generate_tryon: model={len(model_image_bytes)} bytes, {len(clothing_images)} clothing items")
    model_resized = _resize_image(model_image_bytes)
    clothing_resized = [_resize_image(img) for img in clothing_images]

    # 分类衣物: 上装 vs 下装
    top_images = []
    bottom_images = []
    for i, item in enumerate(clothing_items):
        cat = item.get("category", "")
        logger.info(f"  clothing[{i}]: category='{cat}', is_bottom={cat in BOTTOM_CATEGORIES}")
        if cat in BOTTOM_CATEGORIES:
            bottom_images.append(clothing_resized[i])
        else:
            top_images.append(clothing_resized[i])

    logger.info(f"Uploading images: 1 model + {len(top_images)} top + {len(bottom_images)} bottom")

    # Step 1: 上传模特图
    person_url = await _upload_to_dashscope(model_resized, "person.jpg")
    if not person_url:
        return {"success": False, "imageUrl": None, "message": "模特图上传失败"}

    # Step 2: 上传衣物图 (取第一件上装和第一件下装)
    top_url = None
    bottom_url = None

    if top_images:
        top_url = await _upload_to_dashscope(top_images[0], "top_garment.jpg")
        if not top_url:
            logger.warning("Top garment upload failed")

    if bottom_images:
        bottom_url = await _upload_to_dashscope(bottom_images[0], "bottom_garment.jpg")
        if not bottom_url:
            logger.warning("Bottom garment upload failed")

    # 如果都没有上传成功，尝试把所有衣物当上装
    if not top_url and not bottom_url:
        for img in clothing_resized:
            url = await _upload_to_dashscope(img, "garment.jpg")
            if url:
                top_url = url
                break

    if not top_url and not bottom_url:
        return {"success": False, "imageUrl": None, "message": "衣物图上传失败"}

    # Step 3: 调用 aitryon API
    logger.info("Calling aitryon virtual try-on API...")
    result = await _call_aitryon(person_url, top_url, bottom_url)

    if result and result.get("success"):
        return result

    # 如果失败，返回错误信息
    return result or {"success": False, "imageUrl": None, "message": "虚拟试穿生成失败"}
