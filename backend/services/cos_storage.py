"""
腾讯云 COS 对象存储服务
- 上传衣物图片到 COS
- 生成公网可访问的 URL（供试穿使用）
- 从 COS 下载图片
"""
import io
import uuid
import logging
from typing import Optional

from config import get_settings

logger = logging.getLogger("cos_storage")


def _get_cos_client():
    """
    获取 COS 客户端实例
    需要配置: COS_SECRET_ID, COS_SECRET_KEY, COS_REGION, COS_BUCKET
    """
    settings = get_settings()

    if not all([settings.cos_secret_id, settings.cos_secret_key,
                settings.cos_region, settings.cos_bucket]):
        return None, None

    from qcloud_cos import CosConfig, CosS3Client
    config = CosConfig(
        Region=settings.cos_region,
        SecretId=settings.cos_secret_id,
        SecretKey=settings.cos_secret_key,
        Scheme="https",
    )
    client = CosS3Client(config)
    return client, settings.cos_bucket


def is_cos_enabled() -> bool:
    """检查 COS 是否已配置"""
    settings = get_settings()
    return all([settings.cos_secret_id, settings.cos_secret_key,
                settings.cos_region, settings.cos_bucket])


def upload_to_cos(image_bytes: bytes, filename: str = "image.jpg",
                  folder: str = "closet") -> Optional[str]:
    """
    上传图片到 COS，返回公网 URL

    参数:
        image_bytes: 图片字节数据
        filename: 原始文件名
        folder: COS 中的文件夹路径 (如 "closet", "tryon")

    返回:
        公网可访问的 URL，如 https://bucket.cos.ap-shanghai.myqcloud.com/closet/xxx.jpg
        失败返回 None
    """
    client, bucket = _get_cos_client()
    if not client:
        logger.warning("COS not configured, skipping upload")
        return None

    try:
        # 生成唯一的 COS key
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        cos_key = f"{folder}/{uuid.uuid4().hex}.{ext}"

        # 推断 Content-Type
        content_type = "image/jpeg"
        if ext.lower() == "png":
            content_type = "image/png"
        elif ext.lower() == "webp":
            content_type = "image/webp"

        # 上传到 COS
        resp = client.put_object(
            Bucket=bucket,
            Body=image_bytes,
            Key=cos_key,
            ContentType=content_type,
            EnableMD5=False,
        )

        etag = resp.get("ETag", "")
        if etag:
            # 构建公网 URL
            settings = get_settings()
            public_url = (
                f"https://{bucket}.cos.{settings.cos_region}.myqcloud.com/{cos_key}"
            )
            logger.info(f"Uploaded to COS: {public_url}")
            return public_url
        else:
            logger.error(f"COS upload failed, no ETag: {resp}")
            return None

    except Exception as e:
        logger.error(f"COS upload exception: {e}")
        return None


def download_from_cos(url: str) -> Optional[bytes]:
    """
    从 COS 下载图片

    支持:
        - 完整公网 URL: https://bucket.cos.region.myqcloud.com/key
        - COS key: closet/xxx.jpg

    返回:
        图片字节数据，失败返回 None
    """
    client, bucket = _get_cos_client()
    if not client:
        logger.warning("COS not configured, cannot download")
        return None

    try:
        # 从 URL 提取 key
        if url.startswith("http"):
            # https://bucket.cos.region.myqcloud.com/closet/xxx.jpg → closet/xxx.jpg
            parts = url.split(".myqcloud.com/", 1)
            if len(parts) == 2:
                cos_key = parts[1]
            else:
                # 尝试从路径提取
                cos_key = url.split("/")[-1]
                logger.warning(f"Could not parse COS key from URL: {url}")
                return None
        else:
            cos_key = url

        resp = client.get_object(
            Bucket=bucket,
            Key=cos_key,
        )

        # 读取响应体
        body = resp["Body"]
        buf = io.BytesIO()
        while True:
            chunk = body.read(8192)
            if not chunk:
                break
            buf.write(chunk)

        image_bytes = buf.getvalue()
        logger.info(f"Downloaded from COS: {cos_key} ({len(image_bytes)} bytes)")
        return image_bytes

    except Exception as e:
        logger.error(f"COS download exception: {e}")
        return None


def delete_from_cos(url: str) -> bool:
    """从 COS 删除文件"""
    client, bucket = _get_cos_client()
    if not client:
        return False

    try:
        if url.startswith("http"):
            parts = url.split(".myqcloud.com/", 1)
            cos_key = parts[1] if len(parts) == 2 else None
        else:
            cos_key = url

        if not cos_key:
            return False

        client.delete_object(Bucket=bucket, Key=cos_key)
        logger.info(f"Deleted from COS: {cos_key}")
        return True

    except Exception as e:
        logger.error(f"COS delete exception: {e}")
        return False
