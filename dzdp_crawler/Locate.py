import pyautogui
import time
import os
import importlib
import sys
import json

# Define Config.py path relative to this script
SCRIPT_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'Config.py')

# 确保Config.py存在
if not os.path.exists(CONFIG_PATH):
    print(f"Config.py不存在于预期路径 {CONFIG_PATH}，请先确保该文件存在")
    sys.exit(1)

# 导入配置
import Config

def get_position(prompt):
    """提示用户并将鼠标位置保存下来"""
    input(f"{prompt} 将鼠标移动到目标位置，然后按Enter键...")
    position = pyautogui.position()
    print(f"位置已记录: {position}\n")
    return position

def main():
    """主定位函数"""
    print("=== 大众点评搜索界面定位工具 ===")
    print("请按照提示依次定位各个元素")
    print("定位过程中请勿移动或调整模拟器窗口")
    
    # Use a local dictionary to store positions during the script run
    local_positions = {}

    # 定位模拟器边界
    local_positions["simulator_top_left"] = get_position("请定位模拟器左上角")
    local_positions["simulator_bottom_right"] = get_position("请定位模拟器右下角")
    
    # 定位基本元素
    local_positions["city_dropdown_button"] = get_position("请定位城市下拉按钮")
    local_positions["city_search_box"] = get_position("请定位城市搜索框")
    local_positions["city_result"] = get_position("请定位城市搜索结果（选中后的位置）")
    local_positions["food_button"] = get_position("请定位美食按钮")
    local_positions["food_ranking_button"] = get_position("请定位美食排行按钮")
    
    # 定位19个细分品类
    print("\n=== 定位19个细分品类 ===")
    # Add prompt for scrolling
    input("请确保'细分品类'下拉箭头可见 (如有需要请先手动下滑页面)。准备好后按回车继续...") 
    local_positions["category_dropdown"] = get_position("请定位细分品类下拉按钮")
    print("请先点击细分品类下拉按钮展开列表")
    input("展开列表后按回车继续...")
    
    categories = []
    for i in range(19):
        pos = get_position(f"请定位第{i+1}个细分品类")
        categories.append(pos)
    
    local_positions["categories"] = categories
    
    # 定位返回按钮
    print("\n=== 返回按钮定位 ===")
    print("确保当前仍在细分榜单页面")
    local_positions["back_button"] = get_position("请定位页面左上角的'返回'按钮")
    
    print("\n所有位置已定位完成，正在保存配置...")

    # 将位置信息写入Config.py
    config_path = CONFIG_PATH
    try:
        # Check if Config.py exists before reading
        if not os.path.exists(config_path):
             print(f"错误: 配置文件不存在于 {config_path}。请确保文件存在。")
             # Optionally, try to create a default one or exit
             sys.exit(1)
             
        # 读取现有Config.py内容
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 找到positions字典的起始和结束行
        start_line = -1
        end_line = -1
        in_positions_dict = False
        for i, line in enumerate(lines):
            if "positions = {" in line:
                start_line = i
                in_positions_dict = True
            elif in_positions_dict and "}" in line:
                end_line = i
                break
        
        if start_line != -1 and end_line != -1:
            # Create a new dictionary with tuples instead of Point objects
            positions_to_write = {}
            for key, value in local_positions.items():
                if key == "categories" and isinstance(value, list):
                    # Convert Points within the categories list to tuples
                    positions_to_write[key] = [
                        (p.x, p.y) if hasattr(p, 'x') and hasattr(p, 'y') else p 
                        for p in value
                    ]
                elif hasattr(value, 'x') and hasattr(value, 'y'): 
                    # Convert standalone Point object to tuple
                    positions_to_write[key] = (value.x, value.y)
                else:
                    # Keep other values (like None) as is
                    positions_to_write[key] = value

            # Now build the string representation from positions_to_write
            new_positions_str = "positions = {\n"
            items_str = []
            for key, value in positions_to_write.items():
                # Use repr() to get a string representation suitable for Python code
                # This correctly handles tuples, lists, None, etc.
                items_str.append(f'    "{key}": {repr(value)}')
            
            new_positions_str += ",\n".join(items_str) # Join items with comma and newline
            new_positions_str += "\n}"
            
            # Replace the old dictionary part
            new_lines = lines[:start_line] + [new_positions_str + '\n'] + lines[end_line+1:]
            
            # Write back to Config.py
            with open(config_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"位置信息已成功更新到 {config_path}")
        else:
            print(f"错误: 无法在{config_path}中找到'positions'字典结构，请检查文件格式。")
            # Print the dictionary that *would* have been written
            print("请将以下内容手动复制到Config.py中替换'positions'字典：")
            print("positions = {")
            for key, value in local_positions.items(): # Print original for debugging if write fails
                 if key == "categories":
                    print(f'    "{key}": [')
                    print(", ".join([str(p) for p in value]) + "],", file=sys.stderr)
                 else:
                    print(f'    "{key}": {repr(value)},', file=sys.stderr)
            print("}", file=sys.stderr)

    except FileNotFoundError:
        print(f"错误: {config_path} 文件不存在。请确保该文件在 dzdp_crawler 目录中。")
    except Exception as e:
        print(f"更新{config_path}时出错: {e}")
        print("请将以下内容手动复制到Config.py中替换'positions'字典：")
        # Print the collected local_positions dictionary
        print("positions = {")
        for key, value in local_positions.items():
             if key == "categories":
                print(f'    "{key}": [')
                print(", ".join([str(p) for p in value]) + "],", file=sys.stderr)
             else:
                print(f'    "{key}": {repr(value)},', file=sys.stderr)
        print("}", file=sys.stderr)

if __name__ == "__main__":
    main() 