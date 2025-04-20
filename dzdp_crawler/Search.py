import pyautogui
import pyperclip
import time
import os
import sys
from datetime import datetime
import importlib
from PIL import Image, ImageGrab
import platform

# Define Config.py path relative to this script
SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'Config.py')

# 确保Config.py存在
# Corrected Check: Use the absolute CONFIG_PATH
if not os.path.exists(CONFIG_PATH):
    print(f"Config.py不存在于预期路径 {CONFIG_PATH}，请先运行Locate.py进行定位")
    sys.exit(1)

# 导入配置
import Config

# Reload Config in case Locate.py just updated it
importlib.reload(Config)

# 检查所有必要位置是否已经定位 (including back_button)
required_positions = [
    "simulator_top_left", "simulator_bottom_right", "city_dropdown_button",
    "city_search_box", "city_result", "food_button", "food_ranking_button",
    "category_dropdown", "categories", "back_button"
]
missing_positions = [p for p in required_positions if Config.positions.get(p) is None]

if missing_positions:
    print(f"位置尚未完全定位，缺失: {', '.join(missing_positions)}")
    print("请先运行Locate.py进行定位")
    sys.exit(1)

# 确保categories是列表并且有19个元素
if not isinstance(Config.positions.get("categories"), list) or len(Config.positions["categories"]) != 19:
    print("Config.py中的'categories'格式不正确或数量不足19个。请重新运行Locate.py")
    sys.exit(1)

# 创建保存截图的根目录
results_dir = "搜索结果截图"
if not os.path.exists(results_dir):
    os.makedirs(results_dir)

def click_position(position, description="位置"):
    """点击指定坐标，增加健壮性检查"""
    if not isinstance(position, (tuple, list)) or len(position) != 2:
        print(f"错误: 无效的位置坐标 '{description}': {position}。请重新运行Locate.py")
        return False # Indicate failure
    print(f"点击{description}: {position}")
    pyautogui.click(position[0], position[1])
    time.sleep(1)  # 点击后稍作等待
    return True # Indicate success

def copy_and_paste(text):
    """将文本复制到剪贴板并粘贴"""
    print(f"粘贴文本: {text}")
    pyperclip.copy(text)
    time.sleep(0.5)
    
    # 根据操作系统选择不同的粘贴热键
    if platform.system() == "Darwin":  # macOS
        pyautogui.hotkey('command', 'v')
    else:  # Windows/Linux
        pyautogui.hotkey('ctrl', 'v')
    
    time.sleep(1)

def take_screenshot(save_path):
    """截取模拟器窗口的截图并保存"""
    # Check if coordinates are valid before grabbing
    top_left = Config.positions["simulator_top_left"]
    bottom_right = Config.positions["simulator_bottom_right"]
    if not (isinstance(top_left, (tuple, list)) and len(top_left) == 2 and 
            isinstance(bottom_right, (tuple, list)) and len(bottom_right) == 2 and
            bottom_right[0] > top_left[0] and bottom_right[1] > top_left[1]):
        print(f"错误: 无效的模拟器边界坐标 {top_left}, {bottom_right}。请重新运行Locate.py")
        return False # Indicate failure
    
    left, top = top_left
    right, bottom = bottom_right
    
    # 截取指定区域
    try:
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        screenshot.save(save_path)
        print(f"截图已保存: {save_path}")
        time.sleep(0.5)
        return True # Indicate success
    except Exception as e:
        print(f"截图失败: {e}")
        return False # Indicate failure

def perform_search_for_city(city_name):
    """针对单个城市执行搜索和截图逻辑"""
    print(f"\n=== 开始处理城市: {city_name} ===")
    
    # 每次运行时创建带时间戳的文件夹
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(results_dir, f"{city_name}_{timestamp}")
    os.makedirs(session_dir)
    print(f"数据将保存到: {session_dir}")
    
    # --- 城市选择 --- 
    print("\n步骤 1: 选择城市")
    # Get position first
    city_dropdown_pos = Config.positions.get("city_dropdown_button")
    if not city_dropdown_pos:
        print("错误: 未找到 'city_dropdown_button' 坐标。请检查Config.py")
        return False
        
    # Rapid double-click instead of two click_position calls
    print("点击城市下拉按钮 (快速双击)")
    pyautogui.click(city_dropdown_pos[0], city_dropdown_pos[1])
    time.sleep(0.2) # Short delay for double-click
    pyautogui.click(city_dropdown_pos[0], city_dropdown_pos[1])
    time.sleep(1) # Wait after double-click
    
    # Continue with search box, paste, result click
    if not click_position(Config.positions["city_search_box"], "城市搜索框"): return False
    time.sleep(1)
    copy_and_paste(city_name) 
    time.sleep(1)
    if not click_position(Config.positions["city_result"], "城市搜索结果"): return False
    print(f"城市 '{city_name}' 已选择")
    time.sleep(2)  # 等待城市切换完成
    
    # --- 进入美食排行 --- 
    print("\n步骤 2: 进入美食排行")
    if not click_position(Config.positions["food_button"], "美食按钮"): return False
    time.sleep(2)
    if not click_position(Config.positions["food_ranking_button"], "美食排行按钮"): return False
    # 点击多次确保进入
    if not click_position(Config.positions["food_ranking_button"], "美食排行按钮"): return False
    if not click_position(Config.positions["food_ranking_button"], "美食排行按钮"): return False
    print("已进入美食排行页面")
    time.sleep(3)  # 等待页面加载
    
    # --- 主榜单截图 --- 
    print("\n步骤 3: 采集主榜单")
    main_ranking_dir = os.path.join(session_dir, "主榜单")
    os.makedirs(main_ranking_dir)
    print(f"主榜单截图将保存到 {main_ranking_dir}")
    if not take_screenshot(os.path.join(main_ranking_dir, "0.png")): return False # Initial screenshot
    for i in range(Config.main_ranking_scroll_times):
        print(f"主榜单下滑 ({i+1}/{Config.main_ranking_scroll_times})")
        Config.scroll_down()  # 执行下滑
        if not take_screenshot(os.path.join(main_ranking_dir, f"{i+1}.png")): return False # Scroll screenshots
    
    # --- 细分品类截图 --- 
    print("\n步骤 4: 采集细分榜单")
    categories = Config.positions["categories"]
    for category_index in range(len(categories)):
        print(f"\n处理细分品类 {category_index+1}/{len(categories)}")
        # 9. 点击细分品类下拉
        if not click_position(Config.positions["category_dropdown"], "细分品类下拉"): return False
        time.sleep(1)
        
        # 10. 点击具体细分品类
        category_position = categories[category_index]
        if not click_position(category_position, f"细分品类 {category_index+1}"): return False
        print(f"已选择细分品类 {category_index+1}")
        time.sleep(3)  # 等待页面加载
        
        # 创建该细分品类的文件夹
        # Use index+1 for folder name consistency
        category_dir = os.path.join(session_dir, f"细分榜单{category_index+1}") 
        os.makedirs(category_dir)
        print(f"细分榜单截图将保存到 {category_dir}")
        
        # 第一次截图
        if not take_screenshot(os.path.join(category_dir, "0.png")): return False
        
        # 循环滚动和截图
        for i in range(Config.category_ranking_scroll_times):
            print(f"细分品类下滑 ({i+1}/{Config.category_ranking_scroll_times})")
            Config.scroll_down()  # 执行下滑
            if not take_screenshot(os.path.join(category_dir, f"{i+1}.png")): return False
    
    print(f"\n城市 '{city_name}' 数据采集完成!")
    return True # Indicate success for this city

def main():
    """主搜索逻辑 - 循环处理多个城市"""
    print("=== 大众点评多城市搜索自动化脚本 ===")
    print(f"将搜索以下城市: {', '.join(Config.search_cities)}")
    print(f"主榜单下滑次数: {Config.main_ranking_scroll_times}")
    print(f"细分品类榜单下滑次数: {Config.category_ranking_scroll_times}")
    
    # 获取返回按钮位置
    back_button_pos = Config.positions["back_button"]
    if not back_button_pos:
        print("错误: 未找到返回按钮位置，请运行Locate.py")
        sys.exit(1)
        
    total_cities = len(Config.search_cities)
    successful_cities = 0
    failed_cities = []

    for index, city in enumerate(Config.search_cities):
        city_success = perform_search_for_city(city)
        
        if city_success:
            successful_cities += 1
        else:
            failed_cities.append(city)
            print(f"城市 '{city}' 处理失败，跳过后续步骤。")

        # --- 返回主界面 --- (无论成功失败，都尝试返回)
        print(f"\n步骤 5: 返回主界面 (处理完城市: {city})")
        # 点击两次返回按钮，每次间隔1秒
        print("点击返回按钮 (第一次)")
        if not click_position(back_button_pos, "返回按钮"): 
            print("警告: 点击返回按钮失败，可能影响后续处理。")
            # Decide whether to continue or stop
            # sys.exit(1) 
        time.sleep(1)
        print("点击返回按钮 (第二次)")
        if not click_position(back_button_pos, "返回按钮"): 
            print("警告: 点击返回按钮失败，可能影响后续处理。")
            # Decide whether to continue or stop
            # sys.exit(1) 
        time.sleep(2) # 等待返回动画

    # --- 总结 --- 
    print("\n=== 所有城市处理完毕 ===")
    print(f"总共城市: {total_cities}")
    print(f"成功处理: {successful_cities}")
    if failed_cities:
        print(f"失败城市: {', '.join(failed_cities)}")
    else:
        print("所有城市均处理成功！")
    print(f"所有数据已保存到根目录下的 '{results_dir}' 文件夹中对应的城市子文件夹内。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc() 