# Updated by AI: Load .env from one directory up.
# config.py
# Stores configuration for the Xiaohongshu crawler including brand names, like threshold, and cookies

import json
import os
from dotenv import load_dotenv, set_key, find_dotenv

# Construct the path to the .env file in the parent directory
script_dir = os.path.dirname(__file__)
DOTENV_PATH = os.path.join(script_dir, '..', '.env')
DOTENV_PATH = os.path.normpath(DOTENV_PATH) # Normalize path

# Load the .env file from the calculated path
print(f"[config.py] Loading .env from: {DOTENV_PATH}")
load_dotenv(dotenv_path=DOTENV_PATH)

# List of brands to crawl (This will be overwritten by pipeline_controller.py)
BRANDS = [
    "ANOTHER ROOM 别屋",
    "Ameigo 梅果",
    "Ameigo梅果",
    "Hotting 火店",
    "Hygge 薄荷花园餐厅",
    "JAMYAN 伽米 蜜融小馆",
    "Jamyan Bistro&Wine",
    "ONEMORETHAI 泰铺",
    "一口",
    "三出山火锅",
    "三板斧烤鸭煲",
    "上河川",
    "丹青宴",
    "前夫的店",
    "品味老汉口",
    "回味黑鸭煲",
    "夏氏砂锅",
    "大中华酒楼",
    "娟娟姐",
    "小骆川菜馆",
    "山城老泡",
    "山燕 Basjoo",
    "巴厘龙虾",
    "捌川",
    "易下饭 bistro",
    "楚采",
    "毛大估",
    "汉口府",
    "清真双宝红油牛系列",
    "渔歌",
    "渔集逸院",
    "满小二",
    "皮皮大排档",
    "老市井",
    "聚味",
    "肥肥虾庄",
    "花麻布HUAMABU火锅",
    "芸山季",
    "苏眉 Soulmate",
    "草原大漠时光",
    "蓝果子LANGUOZI火锅",
    "蘭府 LANMANSION",
    "蟹神",
    "行",
    "谢萍鲜牛肉串串火锅",
    "贯 Guui",
    "遇南三",
    "野夫 yeego",
    "野果 yeego",
    "野陶",
    "闭云无敌鳝子",
    "靓靓蒸虾",
    "馥 FOOD",
    "鲷归",
] # Updated by main/get_brand.py

# Minimum number of likes required for a post to be crawled
LIKE_THRESHOLD = 500

# Path to the .env file is already stored in DOTENV_PATH
# The code below that tries to find it again is redundant
# # DOTENV_PATH = find_dotenv()
# # if not DOTENV_PATH:
# #     # If .env doesn't exist, create one in the current directory
# #     DOTENV_PATH = os.path.join(os.getcwd(), ".env")
# #     with open(DOTENV_PATH, 'w') as f:
# #         f.write("XHS_COOKIE=\n")
# #     print("Created .env file.")

def save_cookie(cookie_json_str):
    """Save cookie JSON string to the .env file (located at DOTENV_PATH)"""
    try:
        # Use set_key to update the value in the parent .env file
        set_key(DOTENV_PATH, "XHS_COOKIE", cookie_json_str, quote_mode="never")
        print(f"Cookie JSON string saved to {DOTENV_PATH}: {cookie_json_str[:30]}...")
    except Exception as e:
        print(f"Error saving cookie to {DOTENV_PATH}: {e}")

def load_cookie_obj():
    """Load cookie JSON string from .env (located at DOTENV_PATH) and parse it into an object"""
    # Reload dotenv from the specific path to get the latest value
    load_dotenv(dotenv_path=DOTENV_PATH, override=True)
    cookie_json_str = os.getenv("XHS_COOKIE")
    if not cookie_json_str:
        print(f"XHS_COOKIE not found or empty in {DOTENV_PATH}.")
        return None

    try:
        # Parse the JSON string into a Python dictionary
        cookie_obj = json.loads(cookie_json_str)
        # Basic validation
        if not all(k in cookie_obj for k in ["name", "value", "domain", "path"]):
             print("Warning: Loaded cookie object is missing essential fields.")
             return None
        return cookie_obj
    except json.JSONDecodeError:
        print(f"Error: Could not parse the cookie string from {DOTENV_PATH}: {cookie_json_str}")
        return None
    except Exception as e:
        print(f"Error loading or parsing cookie object: {e}")
        return None 