"""
演示衣橱种子数据 - 为游客试玩模式预置示例衣物
启动时若演示账号(demo_user_id)无衣物，则插入一组覆盖全品类的示例衣物。
不调用 AI 识别，直接写入结构化字段，避免消耗 token。
"""
from datetime import datetime

from sqlalchemy import func

from database import SessionLocal
from models.item import ClosetItem
from config import get_settings

# (filename, category, color, season, thickness, description)
# description 复用 closet_service 的「颜色/适用天气」格式，便于复现识别链路
DEMO_ITEMS = [
    ("00e2ee37aac44701848240da214e5fa0.jpg", "short_sleeve", "白色", "夏", "薄",
     "名称: 白色纯棉短袖T恤\n颜色: 白色\n类别: 短袖上衣\n适用天气: 夏季\n厚度: 薄\n材质: 棉\n风格: 简约休闲"),
    ("0efbb9fece80437796c9e6d484fef779.jpg", "long_sleeve", "浅蓝", "春", "薄",
     "名称: 浅蓝色牛津纺长袖衬衫\n颜色: 浅蓝\n类别: 长袖上衣\n适用天气: 春秋\n厚度: 薄\n材质: 棉\n风格: 通勤"),
    ("130607309e5d461f9bd06e1a68662c0b.jpg", "hoodie", "灰色", "秋", "中",
     "名称: 灰色连帽卫衣\n颜色: 灰色\n类别: 卫衣\n适用天气: 秋冬\n厚度: 中\n材质: 棉\n风格: 街头"),
    ("34bc285c99ad4ab08cf4fb35054cd364.jpg", "pants", "黑色", "四季", "中",
     "名称: 黑色修身休闲裤\n颜色: 黑色\n类别: 裤子\n适用天气: 四季\n厚度: 中\n材质: 涤纶混纺\n风格: 百搭"),
    ("3c300c7e336d4520a36dcca0fc031f71.jpg", "pants", "浅蓝", "夏", "薄",
     "名称: 浅蓝色牛仔裤\n颜色: 浅蓝\n类别: 裤子\n适用天气: 春秋\n厚度: 中\n材质: 牛仔布\n风格: 经典"),
    ("43b2991abcf14271b3412774c69f3c14.jpg", "coat", "卡其", "冬", "厚",
     "名称: 卡其色工装棉服\n颜色: 卡其\n类别: 棉服\n适用天气: 冬季\n厚度: 厚\n材质: 防风面料\n风格: 工装"),
    ("523449693f6e47879e8d5a8527e4ab27.jpg", "long_sleeve", "米白", "秋", "中",
     "名称: 米白色针织开衫\n颜色: 米白\n类别: 长袖上衣\n适用天气: 秋冬\n厚度: 中\n材质: 羊毛混纺\n风格: 温柔"),
    ("53dff0cfb4754cbead2bcf9bc1d36f4e.jpg", "dress", "碎花", "夏", "薄",
     "名称: 碎花连衣裙\n颜色: 碎花\n类别: 连衣裙\n适用天气: 夏季\n厚度: 薄\n材质: 雪纺\n风格: 法式"),
    ("54a9412e369748d7a74d09bcb372c141.jpg", "sneakers", "白色", "四季", "薄",
     "名称: 白色运动板鞋\n颜色: 白色\n类别: 运动鞋\n适用天气: 四季\n厚度: 薄\n材质: 帆布/皮革\n风格: 运动"),
    ("89a058a5641549e993d7dee629b8a2cc.jpg", "shoes", "棕色", "四季", "薄",
     "名称: 棕色乐福鞋\n颜色: 棕色\n类别: 鞋靴\n适用天气: 四季\n厚度: 薄\n材质: 牛皮\n风格: 复古"),
    ("9c2a6d94e9884e99b956ee334e41e6e7.jpg", "coat", "黑色", "冬", "厚",
     "名称: 黑色羊毛大衣\n颜色: 黑色\n类别: 棉服\n适用天气: 冬季\n厚度: 厚\n材质: 羊毛\n风格: 极简"),
    ("ad484279818b4de7a5d01ab661e55aa3.jpg", "accessories", "驼色", "秋", "薄",
     "名称: 驼色针织围巾\n颜色: 驼色\n类别: 配饰\n适用天气: 秋冬\n厚度: 薄\n材质: 羊毛\n风格: 保暖"),
    ("af8e24fd575e4ff1b255a6e2aa68cc7e.jpg", "short_sleeve", "条纹", "夏", "薄",
     "名称: 蓝白条纹短袖\n颜色: 条纹\n类别: 短袖上衣\n适用天气: 夏季\n厚度: 薄\n材质: 棉\n风格: 海风"),
    ("bc39ff8ee2ae40d6938169bd1e1bc089.jpg", "pants", "灰色", "四季", "中",
     "名称: 灰色运动卫裤\n颜色: 灰色\n类别: 裤子\n适用天气: 四季\n厚度: 中\n材质: 棉\n风格: 运动"),
    ("c44d3c9032a34fad82fa57e3a09a3cf2.jpg", "hoodie", "藏青", "秋", "中",
     "名称: 藏青连帽卫衣\n颜色: 藏青\n类别: 卫衣\n适用天气: 秋冬\n厚度: 中\n材质: 棉\n风格: 基础"),
    ("d8c6e22a8ff24ed6a77ed04c6e762451.jpg", "dress", "黑色", "四季", "薄",
     "名称: 黑色小礼裙\n颜色: 黑色\n类别: 连衣裙\n适用天气: 四季\n厚度: 薄\n材质: 醋酸\n风格: 优雅"),
]


def ensure_demo_closet():
    """确保演示账号拥有预置衣橱；已存在则跳过。"""
    settings = get_settings()
    demo_user_id = settings.demo_user_id
    db = SessionLocal()
    try:
        count = db.query(func.count(ClosetItem.id)).filter(
            ClosetItem.user_id == demo_user_id
        ).scalar() or 0
        if count > 0:
            print(f"[DEMO] 演示衣橱已存在（{count} 件），跳过种子")
            return

        upload_dir = settings.upload_dir
        inserted = 0
        for filename, category, color, season, thickness, description in DEMO_ITEMS:
            import os
            if not os.path.exists(os.path.join(upload_dir, filename)):
                continue  # 示例图缺失则跳过，不强依赖
            item = ClosetItem(
                user_id=demo_user_id,
                url=f"/uploads/{filename}",
                category=category,
                description=description,
                color=color,
                season=season,
                thickness=thickness,
                created_at=datetime.now(),
            )
            db.add(item)
            inserted += 1
        db.commit()
        print(f"[DEMO] 已预置演示衣橱 {inserted} 件（user_id={demo_user_id}）")
    except Exception as e:
        db.rollback()
        print(f"[DEMO][WARN] 预置演示衣橱失败: {e}")
    finally:
        db.close()
