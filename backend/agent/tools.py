"""
Agent 工具定义 - OpenAI Function Calling 格式
"""

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_closet",
            "description": "在用户衣橱中搜索衣物。支持自然语言描述，如'蓝色牛仔裤'、'适合冬天的外套'。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词或自然语言描述"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["all", "short_sleeve", "long_sleeve", "hoodie", "pants", "shorts", "coat", "sneakers", "shoes", "dress", "accessories"],
                        "description": "限定衣物分类（可选）"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气信息，用于辅助穿搭推荐",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_outfit",
            "description": "根据用户衣橱、天气和出行目的，AI推荐穿搭方案",
            "parameters": {
                "type": "object",
                "properties": {
                    "purpose": {
                        "type": "string",
                        "description": "出行目的，如'上班'、'约会'、'运动'、'日常'"
                    },
                    "city": {
                        "type": "string",
                        "description": "所在城市，用于获取天气"
                    }
                },
                "required": ["purpose"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_closet_categories",
            "description": "列出用户衣橱中所有衣物分类及每个分类的数量",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_outfit_advice",
            "description": "获取穿搭风格和配色建议（不需要搜索衣橱，纯知识问答）",
            "parameters": {
                "type": "object",
                "properties": {
                    "style": {
                        "type": "string",
                        "description": "想了解的穿搭风格，如'商务休闲'、'日系'、'街头'"
                    },
                    "occasion": {
                        "type": "string",
                        "description": "场合，如'面试'、'约会'、'派对'"
                    }
                },
                "required": []
            }
        }
    }
]
