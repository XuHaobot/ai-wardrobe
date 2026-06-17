"""
AI 工具 - 通义千问 VL 衣物识别
"""
import base64
import re
import httpx
from config import get_settings


# 分类关键词映射
CATEGORY_KEYWORDS = {
    "short_sleeve": ["短袖", "T恤", "t恤", "半袖"],
    "long_sleeve": ["长袖", "衬衫", "亨利衫"],
    "hoodie": ["卫衣", "连帽", "帽衫"],
    "pants": ["长裤", "牛仔裤", "西裤", "休闲裤", "运动裤"],
    "shorts": ["短裤", "五分裤", "热裤"],
    "coat": ["夹克", "外套", "风衣", "棉服", "羽绒服", "大衣"],
    "sneakers": ["运动鞋", "跑鞋", "球鞋"],
    "shoes": ["皮鞋", "休闲鞋", "靴子", "鞋"],
    "dress": ["连衣裙", "裙子", "半身裙"],
    "accessories": ["围巾", "帽子", "手套", "领带", "包"],
}


def normalize_category(description: str) -> str:
    """根据AI描述文本推断衣物分类"""
    if not description:
        return "all"
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in description:
                return category
    return "all"


# 颜色关键词列表（用于从描述中提取简洁颜色）
_COLOR_KEYWORDS = [
    "黑色", "白色", "灰色", "红色", "蓝色", "绿色", "黄色", "紫色",
    "粉色", "橙色", "棕色", "卡其色", "米色", "藏青色", "深蓝色",
    "浅蓝色", "深灰色", "浅灰色", "酒红色", "墨绿色", "驼色",
    "军绿色", "咖啡色", "米白色", "杏色", "藕粉色", "烟灰色",
    "深绿色", "浅绿色", "天蓝色", "宝蓝色", "玫红色", "橘色",
]


def _extract_simple_color(color_text: str) -> str:
    """从颜色描述文本中提取简洁的颜色词"""
    if not color_text:
        return ""
    # 在颜色文本中查找已知的颜色关键词，优先匹配最长的
    for color in sorted(_COLOR_KEYWORDS, key=len, reverse=True):
        if color in color_text:
            return color
    # 没匹配到已知颜色，尝试去掉常见冗余词
    cleaned = re.sub(r"(主色调为?|图案颜色为?|以|为主|的|颜色)", "", color_text).strip()
    if cleaned and len(cleaned) <= 6:
        return cleaned
    return ""


def extract_name(description: str) -> str:
    """从AI描述中提取简短衣物名称，例如"黑色夹克"、"蓝色牛仔裤" """
    if not description:
        return "未命名衣物"

    # 尝试从"衣物类型: xxx"行提取
    match = re.search(r"衣物类型[:：]\s*(.+)", description)
    clothing_type = match.group(1).strip() if match else ""

    # 提取颜色并简化
    color_match = re.search(r"颜色[:：]\s*(.+?)(?:[\n，,]|$)", description)
    raw_color = color_match.group(1).strip() if color_match else ""
    color = _extract_simple_color(raw_color)

    if color and clothing_type:
        return f"{color}{clothing_type}"
    elif clothing_type:
        return clothing_type
    return "未命名衣物"


async def recognize_clothing(image_bytes: bytes) -> dict:
    """
    调用通义千问 VL 识别衣物图片
    返回: {"description": str, "category": str, "name": str}
    """
    settings = get_settings()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    prompt = """你是一位专业的服装视觉描述专家。请仔细观察这张衣物图片，输出以下结构化描述：
衣物类型: (例如：长袖衬衫、牛仔裤、连帽卫衣、夹克等)
颜色: (主色调及图案颜色)
材质: (根据视觉效果推测)
款式: (具体款式描述)
设计特点: (独特设计元素)
厚度: (轻薄/中等/较厚)
适用天气: (适合什么季节和天气穿着)

请直接输出描述内容，不要添加额外说明。"""

    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.qwen_vl_model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"image": data_url},
                        {"text": prompt},
                    ],
                }
            ]
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers=headers,
            json=payload,
        )

    data = resp.json()
    description = ""
    try:
        description = data["output"]["choices"][0]["message"]["content"][0]["text"]
    except (KeyError, IndexError, TypeError):
        description = "AI识别失败，请重试"

    category = normalize_category(description)
    name = extract_name(description)

    return {
        "description": f"category: {category}\n{description}",
        "category": category,
        "name": name,
    }
