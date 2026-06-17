"""
衣橱管理路由 - 上传/列表/删除/重命名
"""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import Result
from services.closet_service import ClosetService, _extract_name
from main_deps import get_current_user_id

router = APIRouter()


@router.post("/items")
async def upload_item(
    image: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """上传衣物图片 -> AI识别 -> 存入衣橱"""
    try:
        image_bytes = await image.read()
        item = await ClosetService.add_item(db, user_id, image_bytes, image.filename or "upload.jpg")
        return Result.success({
            "id": item.id,
            "url": item.url,
            "name": _extract_name(item.description or ""),
            "description": item.description,
            "category": item.category,
        })
    except Exception as e:
        return Result.error(f"上传失败: {str(e)}")


@router.get("/closet/items")
async def list_items(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    category: str = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取衣橱列表（分页）"""
    result = ClosetService.get_items(db, user_id, page, size, category)
    return Result.success(result)


@router.delete("/closet/items")
async def delete_item(
    url: str = Query(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """删除衣物"""
    success = ClosetService.delete_item(db, user_id, url)
    if success:
        return Result.success(message="删除成功")
    return Result.error("未找到该衣物")


@router.put("/closet/items/name")
async def rename_item(
    body: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """重命名衣物"""
    item_id = body.get("id")
    name = body.get("name", "")
    if not item_id:
        return Result.error("缺少物品ID")
    success = ClosetService.rename_item(db, user_id, item_id, name)
    if success:
        return Result.success(message="重命名成功")
    return Result.error("未找到该衣物")


@router.post("/closet/rebuild-index")
async def rebuild_vector_index(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """重建向量搜索索引"""
    try:
        from services.vector_store import VectorStore
        items = ClosetService.get_all_items(db, user_id)
        # 补充user_id
        for item in items:
            item["user_id"] = user_id
        vs = VectorStore()
        vs.rebuild_index(items)
        return Result.success({"count": len(items), "message": f"已索引 {len(items)} 件衣物"})
    except Exception as e:
        return Result.error(f"重建索引失败: {str(e)}")
