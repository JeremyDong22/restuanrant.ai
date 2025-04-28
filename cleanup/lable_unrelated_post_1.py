# Created by AI assistant.
# This script defines a list of Chinese keywords related to food, dining, and specific restaurant brands.
# It can be used to help identify posts that are likely relevant to these topics.
# Updates:
# - The Chinese keywords list has been verified to correctly identify food-related content in Chinese posts.
# - Tested on post 5fedd72d0000000001000640 which contains terms like 餐厅 (restaurant), 菜品 (dishes), 
#   披萨 (pizza), and other food-related vocabulary.
# - Added detailed statistics to track posts marked as related/not related
# - Added debug mode option for detailed logging
# - Improved handling to explicitly mark posts without keywords as not related
# - Fixed column naming issue with spaces in column names
# - Added proper command-line argument parsing
# - Modified to only update posts where 'is related' is currently NULL
FOOD_RELATED_KEYWORDS = [
    # 跟食物相关的
    "美食", "美味", "佳肴", "小吃", "甜食", "熟食", "主食", 
    "快餐食品", "休闲食品", "零食", "健康食品", "方便食品", "预制菜",
    "餐食", "夜宵", "早午餐", "正餐", "小食", "特色小食", "地道美食",
    "网红美食", "必吃美食", "街头美食", "夜市美食", "人气美食",
    "食材", "生食", "熟食", "火锅食材", "烧烤食材", "有机食品",
    "高蛋白食品", "素食", "素食料理", "轻食", "低脂餐", "减脂餐",
    "海鲜美食", "烧烤美食", "米食", "面食", "地方小吃", "异国美食",
    "食补", "食疗", "营养餐", "儿童餐", "便当餐", "分餐制", "糖水",
    # 跟菜相关的词
    "点菜", "下饭菜", "菜肴", "小菜", "菜品", "菜单", "凉菜", "热菜", "主菜",
    "招牌菜", "素菜", "荤菜", "家常菜", "私房菜", "湘菜", "川菜", "粤菜", "鲁菜",
    "苏菜", "浙菜", "闽菜", "徽菜", "本帮", "东北菜", "西北菜", "云南菜",
    "贵州菜", "新疆菜", "西餐", "日料", "韩料", "泰餐", "越南菜", "法餐", "意餐", 
    "融合菜", "创意菜", "菜品", "菜式", "菜肴", "菜单", "佳肴", "美食", "料理", "饮食", "口味",
    "热菜", "冷菜", "小菜", "主菜", "家常菜", "私房菜", "招牌菜", "素菜", "荤菜", "时令菜",
    "爆款菜", "必点菜", "人气菜", "网红菜", "新品菜", "私藏菜", "下饭菜", "配菜", "快手菜", "养生菜",
    "甜品", "点心", "凉菜", "热炒", "小炒", "蒸菜", "炖菜", "烧菜", "煲菜", "铁板菜",
    "卤味", "麻辣烫", "串串香", "火锅菜", "小火锅菜", "汤菜", "小碟菜",
    "川菜", "粤菜", "湘菜", "鲁菜", "浙菜", "闽菜", "苏菜", "徽菜", "潮菜", "港式菜",
    "台式菜", "日料", "韩料", "泰菜", "越南菜", "意大利菜", "法式菜", "西餐菜",
    "地道菜", "特色菜", "创新菜", "创意菜", "融合菜", "传统菜", "经典菜",
    # 跟饼相关的词
    "煎饼", "葱油饼", "手抓饼", "肉夹馍", "烙饼", "发面饼",
    "馅饼", "烧饼", "糖饼", "梅菜饼", "南瓜饼", "芝麻饼", "花卷",
    "蛋饼", "薄饼", "酥饼", "锅盔", "月饼", "冰皮月饼", "老婆饼",
    "葱花饼", "鸡蛋灌饼", "千层饼", "牛舌饼", "红糖饼", "煎饼果子",
    "葱抓饼", "豆沙饼", "鲜肉月饼", "绿豆饼", "紫薯饼", "芝士饼",
    "馅饼套餐", "肉饼套餐", "芝麻烧饼", "甜酥饼", "咸酥饼",
    # 跟饭相关的词
    "米饭", "盖饭", "炒饭", "蛋炒饭", "扬州炒饭", "石锅拌饭",
    "拌饭", "咖喱饭", "叉烧饭", "牛肉饭", "鸡肉饭", "排骨饭",
    "煲仔饭", "腊味煲仔饭", "卤肉饭", "便当饭", "猪排饭", "烧肉饭",
    "鳗鱼饭", "鲑鱼饭", "焖饭", "泡饭", "杂粮饭", "糯米饭",
    "麻油鸡饭", "海南鸡饭", "生鱼片饭", "鳗鱼蒲烧饭", "三文鱼饭",
    "烤肉饭", "石锅饭", "黑椒牛柳饭", "牛丼饭", "亲子饭", "日式便当饭",
    "铁板饭", "芝士焗饭", "锅巴饭", "腊味饭", "干锅饭",
    # 跟粉相关的词
    "米粉", "肠粉", "螺蛳粉", "桂林米粉", "云南米线", "过桥米线",
    "炒米粉", "炒粉", "河粉", "炒河粉", "牛河", "沙河粉", "宽粉",
    "酸辣粉", "红薯粉", "粉丝", "炒粉丝", "粉皮", "凉皮", "米线",
    "米粉汤", "牛肉粉", "鸡丝粉", "豆花粉", "麻辣烫粉",
    "桂林米粉套餐", "柳州螺蛳粉", "卤味米粉", "老友粉", "酸汤粉",
    "干拌米线", "香锅粉", "小卷粉", "羊肉米粉", "麻辣粉", "香辣米线",
    "过桥米线套餐", "虾滑米线", "芝士米线", "三鲜粉丝汤", "川味米粉"
    # 跟粥相关的词
    "白粥", "皮蛋瘦肉粥", "生滚粥", "艇仔粥", "鱼片粥", 
    "虾仁粥", "牛肉粥", "咸粥", "八宝粥", "莲子粥", "红枣粥",
    "小米粥", "南瓜粥", "黑米粥", "紫米粥", "瘦肉粥", "杂粮粥",
    "排骨粥", "海鲜粥", "砂锅粥", "潮汕粥", "广式粥", "养生粥",
    # 跟汤相关的词
    "老火汤", "炖汤", "炖盅汤", "煲汤", "鸡汤", "排骨汤", 
    "牛腩汤", "羊肉汤", "猪骨汤", "鱼汤", "菌菇汤", "海鲜汤", 
    "清汤", "浓汤", "番茄蛋汤", "紫菜蛋花汤", "玉米排骨汤",
    "冬瓜汤", "苦瓜汤", "骨头汤", "花胶汤", "虫草花汤",
    "养生汤", "滋补汤", "药膳汤", "煲仔汤", "鱼汤", "鱼头汤", "鱼头煲",
    "鱼头豆腐汤", "鱼头豆腐煲", 
    # 跟羹相关的词
    "羹",
    # 跟肉相关的词
    "猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉", "鹅肉", 
    "烤肉", "炖肉", "卤肉", "红烧肉", "叉烧", "烧鸭", 
    "白切鸡", "手抓羊肉", "香辣牛肉", "黑椒牛肉", "蒜香排骨",
    "酱爆肉", "烤全羊", "烤乳猪", "爆炒猪肝", "梅菜扣肉",
    "东坡肉", "铁板牛肉", "煎牛排", "肥牛", "五花肉",
    # 跟蛋相关的词
    "鸡蛋", "咸蛋", "皮蛋", "卤蛋", "溏心蛋", "煎蛋", 
    "蒸蛋", "炒蛋", "蛋花", "蛋包饭", "蛋卷", "蛋挞", "松花蛋",
    "红心咸蛋", "茶叶蛋", "虎皮蛋", "流心蛋", "糖心蛋", "蛋黄酥",
    "烤蛋", "爆浆蛋",
    # 跟奶相关的词
    "牛奶", "羊奶", "豆奶", "燕麦奶", "椰奶", "杏仁奶",
    "乳酪", "酸奶", "奶酪", "芝士", "奶油", "奶盖", "鲜奶",
    "炼乳", "奶昔", "奶冻", "奶茶", "牛奶布丁", "芝士蛋糕",
    "奶黄包", "奶香面包", "厚乳拿铁", "奶香蛋糕", "奶香",
    # 跟鱼相关的词
    "烤鱼", "清蒸鱼", "红烧鱼", "剁椒鱼头", "酸菜鱼", 
    "水煮鱼", "香煎鱼", "糖醋鱼", "干烧鱼", "铁板鱼", 
    "椒麻鱼", "鲈鱼", "鲑鱼", "鳕鱼", "比目鱼", "鲷鱼",
    "草鱼", "鲤鱼", "鲢鱼", "鲫鱼", "黄骨鱼", "黑鱼", 
    "鲟鱼", "石斑鱼", "三文鱼", "金枪鱼", "秋刀鱼",
    "烤鳗鱼", "蒲烧鳗鱼", "烤三文鱼", "炙烤鳗鱼",
    "鱼片粥", "鱼片汤", "鱼头煲", "鱼火锅", "鱼丸",
    "鱼籽", "鱼生", "刺身鱼", "炖鱼", "鱼滑", "炸鱼排",
    "鱼头",
    
    # 跟海鲜相关的词
    "海鲜", "生蚝", "扇贝", "鲍鱼", "海参", "龙虾", "小龙虾", 
    "皮皮虾", "螃蟹", "青蟹", "花蟹", "大闸蟹", "梭子蟹",
    "基围虾", "对虾", "明虾", "白虾", "北极贝", "海螺",
    "象拔蚌", "花甲", "蛤蜊", "扇贝柱", "蚬子", "鲍鱼仔",
    "鱿鱼", "章鱼", "墨鱼", "海胆", "鱼子酱", "蟹黄",
    "蒸虾", "白灼虾", "椒盐虾", "蒜蓉蒸虾", "清蒸螃蟹",
    "蒜蓉", "香辣蟹", "避风塘", "盐焗虾", "香煎鲍鱼",
    "铁板鱿鱼", "爆炒花甲", "蒜蓉粉丝扇贝", "生腌小海鲜",
    "烤生蚝", "拼盘", "烤虾", "海鱼", "海鲜锅",
    "烩饭", "海鲜粥", "海鲜意面", "海鲜汤", "海鲜火锅"

    # 跟内脏相关的词
    "内脏", "猪肝", "猪心", "猪肚", "猪腰", "猪肺", "猪血", 
    "牛肚", "牛百叶", "毛肚", "黄喉", "牛心", "牛肝", "牛腰",
    "羊肚", "羊杂", "鸡胗", "鸡肝", "鸡心", "鸭血", "鸭胗", "鸭肠",
    "鹅肝", "鹅肠", "鱼泡", "鱼鳔", "鱼肚",
    "爆炒猪肝", "香煎鹅肝", "麻辣毛肚", "红烧肥肠", "卤肥肠", 
    "火锅毛肚", "火锅黄喉", "椒麻鸡胗", "爆炒腰花", "葱爆猪心",
    "炖猪肚", "卤鸭胗", "酸菜鸭血粉丝汤", "干锅肥肠", "凉拌毛肚",
    "牛杂煲", "羊杂汤", "猪杂汤", "牛杂火锅", "猪脑花",
    # 跟蔬菜相关的词
     "蔬菜", "青菜", "时蔬", "有机蔬菜", "时令蔬菜", "绿色蔬菜",
    "生菜", "油麦菜", "菠菜", "空心菜", "小白菜", "娃娃菜", "芥兰",
    "苋菜", "莴笋", "芹菜", "西兰花", "花椰菜", "菜花", "西红柿",
    "黄瓜", "丝瓜", "冬瓜", "苦瓜", "南瓜", "茄子", "土豆", "红薯",
    "紫薯", "山药", "莲藕", "胡萝卜", "白萝卜", "香菇", "金针菇",
    "木耳", "银耳", "竹笋", "蘑菇", "豌豆", "毛豆", "四季豆",
    "甜豆", "黄豆芽", "绿豆芽", "豆苗", "地瓜叶", "红菜苔",
    "拌时蔬", "蒜蓉西兰花", "凉拌黄瓜", "炝拌菠菜", "炒时蔬",
    "炖菜花", "地三鲜", "干煸四季豆", "凉拌木耳", "蒜蓉油麦菜",


    "蔬菜", "水果", "点心", "甜点", "甜品", "小吃", "零食", "饮料", "饮品", "酒", "茶", "咖啡", "奶茶",
    "面包", "蛋糕", "饼干", "冰淇淋", "酸奶", "火锅", "烧烤", "烤肉", "串串", "麻辣烫", "冒菜", "干锅",
    "寿司", "刺身", "拉面", "乌冬面", "意面", "披萨", "汉堡", "三明治", "沙拉", "牛排", "羊排", "鸡排",
    "早餐", "午餐", "晚餐", "宵夜", "下午茶", "早茶", "夜宵", "自助餐", "放题", "料理", 
    "素食", "鸡脆骨", "鸡胗",

    # “面”有多义词，这里将它周围的词群列出来，不单独写
    "面条", "面粉", "细面", "手工面", "擀面", "炒面", "捞面", "拉面", 
    "刀削面", "热干面", "炸酱面", "担担面", "方便面", "拌面",
    "肉面", "刀削面", "重庆小面", "兰州拉面", "油面", 
    "凉面", "冷面", "酸辣粉面", "拌面", "汤面", "宽面", "细面",
    "龙须面", "阳春面", "手擀面", "焖面", "干拌面", "干炒面",
    "虾仁炒面", "海鲜炒面", "猪扒拌面", "麻辣拌面", "台式卤肉面",
    "意大利面", "白酱意面", "红酱意面", "酱面", "烤面", 
    "意面", "焗面", "炸酱面", "乌冬面", "荞麦面",
    "泡面", "方便面", "锅面", "火锅面", "蒸面", "炒面",

    # Eating/Dining Verbs & Actions
    "吃到", "喝到", "尝到", "品尝", "用餐", "吃饭", "聚餐", "约饭", "宴请", "下馆子", "开吃", "吃了", 
    "觅食", "吃喝玩乐", "逛吃", "撸串", "点餐", "外卖", "打包", "约饭", "饭搭子",
        # 跟涮相关
        "火锅涮", "手涮", "鲜涮", "即涮即食", "现涮", "涮肉", "麻辣涮","铜锅","锅气"
        # 跟煮相关
        "水煮", "慢煮", "快煮", "炖煮", "滚煮", "温火慢煮", "现煮",
        "清水煮", "香煮",
        # 跟烤相关
        "烧烤", "碳烤", "炭火烤", "铁板烤", "明火烤", "现烤", 
        "炙烤", "烟熏烤", "高温烤", "慢火烤", "火山烤",
        # 跟炸相关
        "油炸", "酥炸", "香炸", "现炸", "爆炸", "轻炸", "慢炸",
        "高温炸", "脆炸", "酥脆炸", "炸至金黄",  
        # 跟蒸相关
        "清蒸", "白灼蒸", "慢蒸", "现蒸", "隔水蒸", "火候蒸", "原味蒸",
        "鲜蒸", "盐水蒸",
        # 跟炖相关
        "慢炖", "小火炖", "温火炖", "老火炖", "清炖", "浓炖", 
        "原汤炖", "养生炖", "滋补炖", "鲜炖",
        #跟炒相关
        "快炒", "猛火炒", "爆炒", "干炒", "清炒", "香炒", 
        "热炒", "滑炒", "酱炒", "现炒",
 

    # Taste & Experience
    "好吃", "美味", "味道", "口味", "风味", "口感", "必吃", 
        # 跟味道相关的二字及以上词汇
        "香辣", "麻辣", "酸辣", "甜辣", "咸香", 
        "鲜香", "香甜", "酸甜", "清淡", "重口味", "微辣", "特辣", 
        "清香", "咸鲜", "鲜美", "浓郁", "爽口", "回甜", "回甘", 
        "甘甜", "奶香", "果香", "酒香", "酱香", "孜然香", "焦香",
        "烟熏味", "醇香", "浓香", "苦甜", "咸甜", "微咸", "清新口感",
        "酥脆", "嫩滑", "软糯", "绵密", "饱满", "丰富口感",
        "多汁", "爆汁", "汁浓", "香酥", "脆爽", "弹牙", "筋道",
        "浓油赤酱", "原汁原味", "鲜嫩多汁", "开胃", "解腻", "下饭", 
        "微辣", "中辣", "重辣", "特辣", "超辣", "爆辣",
        "小辣", "很辣", "稍微辣", "辣死人", "辣到流泪", "变态辣", "火辣",
        "微酸", "很酸", "特酸", "超酸", "爆酸", 
        "酸溜溜", "酸爽", "酸得起飞", "酸到牙疼", "酸爆了",
        "微甜", "偏甜", "很甜", "爆甜", "特甜", "超甜",
        "齁甜", "甜到腻", "甜死人", "齁到发腻", "甜腻", "奶甜",
        "微苦", "偏苦", "很苦", "特苦", "爆苦", "超苦",
        "苦涩", "苦到发麻", "苦到掉眉毛", "苦爆了", "浓苦",
        "微咸", "偏咸", "很咸", "特咸", "超咸", "爆咸",
        "齁咸", "咸到爆", "咸死人", "咸出天际", "齁到不行",
        "微鲜", "很鲜", "特鲜", "超鲜", "爆鲜",
        "鲜美", "鲜香", "鲜甜", "鲜掉眉毛", "鲜到爆汁", "鲜嫩",

    # Restaurant/Place Types
    "餐厅", "饭店", "餐馆", "酒楼", "食堂", "小吃店", "大排档", "排挡", "小馆子", "苍蝇馆子",
    "咖啡馆", "咖啡厅", "茶馆", "茶楼", "茶社", "面包店", "烘焙坊", "甜品店", "糖水铺",
    "酒吧", "小酒馆", "居酒屋", "夜市", "美食街", "食集", "厨房", "料理店", "食堂", "饭堂",
  

    # Hashtags (without '#')
    "美食", "吃货", 
    "真香小吃大集合", "跟我来探店", "网红探店", "宝藏餐厅分享", "氛围感餐厅", 
    "餐厅", "食堂", "一起去探店", "味蕾", "舌尖", "bistro", "Bistro", "brunch",  "Brunch", "cafe",
     "Cafe", "Bar", "Pub", "排队","打卡"

] 


# This script fetches posts from a Supabase table, checks if their content contains specific keywords,
# and updates a boolean column ('is_related') accordingly, but ONLY if the column is currently NULL.
# Updated: Changed PRIMARY_KEY_COLUMN from 'id' to 'post_id'.
# Updated: Added pagination to fetch all posts, not just the first 1000.
# Updated: Fixed issue with column name containing spaces.
# Updated: Added logic to only update if 'is related' is NULL.

import os
import argparse
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment variables.")

# Initialize Supabase client
supabase: Client = create_client(url, key)

# Table configuration
TABLE_NAME = 'posts'
CONTENT_COLUMN = 'content'
IS_RELATED_COLUMN = 'is related'  # Column name with space
PRIMARY_KEY_COLUMN = 'post_id'    # Corrected based on schema info


def check_and_update_posts(debug=False, test_post_id=None):
    """
    Fetches posts where 'is related' is NULL, checks for keywords, and updates the column.
    
    Args:
        debug (bool): If True, prints additional debug information during processing.
        test_post_id (str, optional): If provided, only process this specific post ID (if 'is related' is NULL).
    """
    start_index = 0
    chunk_size = 1000 # Fetch 1000 posts at a time (Supabase default limit)
    total_processed = 0
    total_updated_successfully = 0
    total_errors = 0
    total_related = 0      # Count of posts updated to related=True
    total_not_related = 0  # Count of posts updated to related=False
    total_already_set = 0  # Count of posts skipped because 'is related' was not NULL

    print(f"Starting post processing. Fetching posts where '{IS_RELATED_COLUMN}' is NULL in chunks of {chunk_size}...")
    if debug:
        print(f"Debug mode: ON - Will show detailed information for each post")
    if test_post_id:
        print(f"Test mode: Processing only post ID: {test_post_id}")

    # For testing a specific post
    if test_post_id:
        try:
            print(f"Fetching specific post ID: {test_post_id}")
            # Fetch the specific post, including its 'is related' status
            response = supabase.table(TABLE_NAME)\
                             .select(f'{PRIMARY_KEY_COLUMN}, {CONTENT_COLUMN}, "{IS_RELATED_COLUMN}"')\
                             .eq(PRIMARY_KEY_COLUMN, test_post_id)\
                             .execute()
            
            if not response.data:
                print(f"Post with ID {test_post_id} not found.")
                return
            
            # Process the specific post (process_posts will check if it's NULL)
            process_posts(response.data, debug=True)
            return
            
        except Exception as e:
            print(f"Error fetching specific post ID {test_post_id}: {e}")
            return

    # Normal processing for posts where 'is related' is NULL
    while True:
        try:
            # Fetch a chunk of posts where 'is related' is NULL
            print(f"Fetching posts from index {start_index} where '{IS_RELATED_COLUMN}' is NULL...", end=" ")
            response = supabase.table(TABLE_NAME)\
                             .select(f'{PRIMARY_KEY_COLUMN}, {CONTENT_COLUMN}, "{IS_RELATED_COLUMN}"')\
                             .is_(IS_RELATED_COLUMN, 'null')\
                             .range(start_index, start_index + chunk_size - 1)\
                             .execute()

            if not response.data:
                print("No more posts found with NULL 'is related'.")
                break  # Exit loop if no more data

            posts_in_chunk = len(response.data)
            total_processed += posts_in_chunk
            print(f"Fetched {posts_in_chunk} posts.")

            # Process the current chunk of posts
            chunk_stats = process_posts(response.data, debug)
            
            # Update statistics
            total_updated_successfully += chunk_stats['updated']
            total_errors += chunk_stats['errors']
            total_related += chunk_stats['related']
            total_not_related += chunk_stats['not_related']
            total_already_set += chunk_stats['already_set'] # Add count for already set posts
            
            # Since we filter by NULL, we don't need to paginate in the traditional sense
            # If a chunk had less than chunk_size, it means we've processed all NULL ones.
            if len(response.data) < chunk_size:
                print("Processed the last chunk of NULL 'is related' posts.")
                break
            
            # If we fetched a full chunk, there might be more, so continue pagination
            start_index += chunk_size 

        except Exception as e:
            print(f"\nAn error occurred during fetching/processing chunk starting at index {start_index}: {e}")
            total_errors += 1 # Count this as an error if fetching fails
            print("Stopping further processing due to error.")
            break

    print(f"\n\nProcessing complete.")
    print(f"Total posts checked (where '{IS_RELATED_COLUMN}' was NULL): {total_processed}")
    print(f"Total posts updated to related=True: {total_related}")
    print(f"Total posts updated to related=False: {total_not_related}")
    # print(f"Total posts skipped (already set): {total_already_set}") # Optional: uncomment to show skipped count
    print(f"Total posts updated successfully: {total_updated_successfully}")
    print(f"Total errors encountered: {total_errors}")


def process_posts(posts, debug=False):
    """
    Process a list of posts, checking for keywords and updating the is_related column
    ONLY if the column is currently NULL.
    
    Args:
        posts (list): List of post objects from Supabase
        debug (bool): Whether to print detailed debug information
        
    Returns:
        dict: Statistics about the processed posts
    """
    statistics = {
        'related': 0,
        'not_related': 0,
        'updated': 0,
        'errors': 0,
        'already_set': 0 # Track posts already set
    }
    
    # For batch statistics
    updates = []
    
    for post in posts:
        try:
            post_id = post[PRIMARY_KEY_COLUMN]
            content = post.get(CONTENT_COLUMN, "")
            current_is_related = post.get(IS_RELATED_COLUMN)

            # --- Check if 'is related' is already set --- 
            if current_is_related is not None:
                if debug:
                    print(f"Skipping post ID {post_id}: '{IS_RELATED_COLUMN}' is already set to {current_is_related}.")
                statistics['already_set'] += 1
                continue # Skip this post
            # --- End Check --- 

            if not isinstance(content, str):
                print(f"Skipping post ID {post_id}: Content is not a string (type: {type(content)}).")
                continue

            content_lower = content.lower()
            
            # Find any keywords in the content
            found_keywords = []
            for keyword in FOOD_RELATED_KEYWORDS:
                if keyword.lower() in content_lower:
                    found_keywords.append(keyword)
                    if len(found_keywords) >= 5 and not debug:  # Limit to 5 keywords unless in debug mode
                        break
            
            # Determine if the post is related to food based on keywords
            is_related = len(found_keywords) > 0
            
            # Track statistics (only for those being updated)
            if is_related:
                statistics['related'] += 1
            else:
                statistics['not_related'] += 1
            
            # Debug output if enabled
            if debug:
                print(f"\nPost {post_id}:")
                print(f"  Content snippet: {content[:100]}...")
                if is_related:
                    print(f"  RELATED - Found {len(found_keywords)} keywords: {', '.join(found_keywords[:10])}")
                    if len(found_keywords) > 10:
                        print(f"    ...and {len(found_keywords) - 10} more keywords")
                else:
                    print(f"  NOT RELATED - No keywords found. Updating '{IS_RELATED_COLUMN}' to False.")

            # Add to update batch (only happens if current_is_related was None)
            updates.append({PRIMARY_KEY_COLUMN: post_id, IS_RELATED_COLUMN: is_related})
        except Exception as e:
            print(f"Error processing post: {e}")
            statistics['errors'] += 1
    
    # Update the posts in batches
    if updates:
        print(f"  Attempting to update {len(updates)} posts (where '{IS_RELATED_COLUMN}' was NULL)...")
        print(f"  - {statistics['related']} posts will be updated to related=True")
        print(f"  - {statistics['not_related']} posts will be updated to related=False")
        
        for update_data in updates:
            post_id_val = update_data[PRIMARY_KEY_COLUMN]
            is_related_val = update_data[IS_RELATED_COLUMN]
            try:
                # Note: Supabase JS/Python client automatically handles column names with spaces
                result = supabase.table(TABLE_NAME)\
                         .update({IS_RELATED_COLUMN: is_related_val})\
                         .eq(PRIMARY_KEY_COLUMN, post_id_val)\
                         .execute()
                
                if debug:
                    print(f"  Update result for post {post_id_val}: {result}")
                
                statistics['updated'] += 1
            except Exception as e:
                print(f"    Error updating post ID {post_id_val}: {e}")
                statistics['errors'] += 1
        
        print(f"  Update complete: {statistics['updated']} success, {statistics['errors']} errors.")
    else:
         print("  No updates needed for this batch (either no posts with NULL 'is related' or all processed)." )
    
    return statistics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update the "is_related" field for posts based on food-related keywords.')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode to show detailed information for each post')
    parser.add_argument('--post', type=str, help='Process only a specific post ID for testing')
    
    args = parser.parse_args()
    
    check_and_update_posts(debug=args.debug, test_post_id=args.post)