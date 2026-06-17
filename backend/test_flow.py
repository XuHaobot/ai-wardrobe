"""
集成测试脚本 - AI智能衣橱功能联调
测试完整流程: 登录 -> 上传 -> 识别 -> 衣柜列表 -> 虚拟试穿
"""
import requests
import json
import time
import sys

BASE = "http://localhost:8080"

def log(msg):
    print(f"[TEST] {msg}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ============================================================
# 1. 登录
# ============================================================
section("1. 用户登录")
resp = requests.post(f"{BASE}/users/login", json={"username": "testuser", "password": "123456"})
data = resp.json()
if data["code"] != 1:
    log(f"Login failed: {data}")
    sys.exit(1)

token = data["data"]["token"]
headers = {"Authorization": token}
user_id = data["data"]["user_id"]
log(f"Login OK: user_id={user_id}")

# ============================================================
# 2. 上传衣物
# ============================================================
section("2. 上传衣物图片 -> AI识别")
import os
test_images = []
for f in os.listdir("uploads"):
    if f.endswith(".jpg") and not f.startswith("tryon_"):
        test_images.append(f)
        if len(test_images) >= 3:
            break

uploaded_items = []
for img_name in test_images:
    img_path = os.path.join("uploads", img_name)
    with open(img_path, "rb") as f:
        resp = requests.post(
            f"{BASE}/items",
            headers=headers,
            files={"image": (img_name, f, "image/jpeg")}
        )
    result = resp.json()
    if result["code"] == 1:
        item = result["data"]
        uploaded_items.append(item)
        log(f"OK: {img_name} -> id={item['id']}, cat={item['category']}, name={item.get('name','?')[:30]}")
    else:
        log(f"FAIL: {img_name} -> {result['message']}")

log(f"Uploaded {len(uploaded_items)} items total")

# ============================================================
# 3. 查询衣柜
# ============================================================
section("3. 查询衣柜列表")
resp = requests.get(f"{BASE}/closet/items", headers=headers, params={"page": 1, "size": 100})
result = resp.json()
if result["code"] == 1:
    closet = result["data"]
    log(f"Total items in closet: {closet['count']}")
    for i in closet["items"][:5]:
        log(f"  id={i['id']}, cat={i['category']}, url={i['url'][:50]}")
    if closet["count"] > 5:
        log(f"  ... and {closet['count'] - 5} more")
else:
    log(f"FAIL: {result}")

# ============================================================
# 4. 虚拟试穿
# ============================================================
section("4. 虚拟试穿")

# 收集所有衣物URL
all_urls = []
resp = requests.get(f"{BASE}/closet/items", headers=headers, params={"page": 1, "size": 100})
closet_data = resp.json()["data"]
for item in closet_data["items"]:
    all_urls.append(item["url"])

if all_urls:
    log(f"Trying try-on with {len(all_urls)} clothing item(s)")
    log(f"First URL: {all_urls[0]}")

    tryon_req = {
        "gender": "female",
        "clothingUrls": all_urls[:2]  # 最多2件
    }

    start_time = time.time()
    resp = requests.post(f"{BASE}/tryon", headers=headers, json=tryon_req, timeout=180)
    elapsed = time.time() - start_time

    result = resp.json()
    if result["code"] == 1:
        tryon_data = result["data"]
        if tryon_data.get("success"):
            log(f"TRY-ON SUCCESS! ({elapsed:.1f}s)")
            log(f"Result image: {tryon_data.get('imageUrl', 'N/A')}")
        else:
            log(f"TRY-ON FAILED ({elapsed:.1f}s)")
            log(f"Message: {tryon_data.get('message', 'unknown error')}")
    else:
        log(f"API Error: {result}")
else:
    log("No clothing items to try on")

# ============================================================
# 5. 按分类查询
# ============================================================
section("5. 按分类查询")
categories = ["pants", "short_sleeve", "long_sleeve", "coat", "hoodie"]
for cat in categories:
    resp = requests.get(f"{BASE}/closet/items", headers=headers, params={"page": 1, "size": 100, "category": cat})
    result = resp.json()
    if result["code"] == 1:
        count = result["data"]["count"]
        if count > 0:
            log(f"Category '{cat}': {count} items")

# ============================================================
# 6. 重命名
# ============================================================
section("6. 重命名衣物")
if uploaded_items:
    item_id = uploaded_items[0]["id"]
    resp = requests.put(
        f"{BASE}/closet/items/name",
        headers=headers,
        json={"id": item_id, "name": "Test Rename Item"}
    )
    result = resp.json()
    log(f"Rename id={item_id}: {'OK' if result['code']==1 else 'FAIL'} -> {result.get('message','')}")

# ============================================================
# 7. 向量索引
# ============================================================
section("7. 重建向量索引")
resp = requests.post(f"{BASE}/closet/rebuild-index", headers=headers)
result = resp.json()
if result["code"] == 1:
    log(f"Vector index: {result['data'].get('message', 'OK')}")
else:
    log(f"Vector index FAIL: {result}")

# ============================================================
# 汇总
# ============================================================
section("测试结果汇总")
print("Done. Check backend logs for detailed error info.")
