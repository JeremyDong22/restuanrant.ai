# Updated by AI assistant on [Date].
# Added automation configuration settings: RELOCATE_EMULATOR, GET_NEW_XHS_COOKIE, OPEN_NEW_BROWSER, PERFORM_CLEANUP.
# main/config.py
# Defines the list of Dianping rankings to extract brands from for XHS crawler.
# Also defines the list of cities for the DZDP crawler.
# Defines automation behavior flags.

# List of ranking names (榜单名称) from dzdpdata to select brands from.
# Ensure these names exactly match the '榜单' column values in your dzdpdata table.
SELECTED_RANKINGS = [
    "主榜单", # Main ranking
    "火锅",   # Hot Pot
    "烤肉",  
    "创意菜",
    "特色菜", 
    # Add more ranking names as needed, e.g., "川菜", "日料"
]

# List of cities (城市名称) for the dzdp_crawler to process.
# 所有备选城市：上海，深圳，成都，重庆，长沙
CITIES = [#"上海",
          #"深圳",
          "成都",
          #"重庆",
          #"长沙"
          ]

# --- Automation Settings ---

# Set to True to automatically relocate the emulator at the start, False to skip.
RELOCATE_EMULATOR = False

# Set to True to automatically obtain a new Xiaohongshu cookie, False to use existing.
# Normally, we turn it on for the first time we run the pipeline.
GET_NEW_XHS_COOKIE = False

# Set to True to open a new permanent browser window for Xiaohongshu interaction, False otherwise.
# Normally, we turn it on for the first time we run the pipeline, the browser will be opened in the background.
OPEN_NEW_BROWSER = True

# Set to True to perform cleanup operations (e.g., closing emulator/browser) at the end, False to skip.
# Normally, we want to perform cleanup at the end of the pipeline.
PERFORM_CLEANUP = True

# !!!save after editing!!!