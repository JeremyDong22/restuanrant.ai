import collections

# Define Point named tuple to represent coordinates
Point = collections.namedtuple("Point", ["x", "y"])

import pyperclip
import pyautogui
import time

# 基础配置
# 要搜索的城市 - 这个在main/main.py中被设置
search_cities = [
    "武汉",
    "成都",
] # Updated by main/main.py
main_ranking_scroll_times = 9  # 主榜单下滑次数
category_ranking_scroll_times = 3  # 细分品类榜单下滑次数

# 坐标配置 (back_button 将由 Locate.py 定位)
positions = {
    "simulator_top_left": (40, 105),
    "simulator_bottom_right": (330, 742),
    "city_dropdown_button": (65, 150),
    "city_search_box": (103, 155),
    "city_result": (63, 192),
    "food_button": (69, 201),
    "food_ranking_button": (70, 212),
    "category_dropdown": (321, 187),
    "categories": [(215, 241), (294, 246), (75, 285), (143, 285), (220, 282), (281, 280), (81, 319), (141, 322), (221, 316), (299, 315), (81, 352), (144, 353), (218, 350), (299, 350), (76, 392), (138, 390), (217, 386), (282, 392), (290, 391)],
    "back_button": (56, 149)
}

# 获取模拟器中心点坐标
def get_simulator_center():
    """计算并返回模拟器窗口的中心点坐标"""
    left, top = positions["simulator_top_left"]
    right, bottom = positions["simulator_bottom_right"]
    center_x = left + (right - left) // 2
    center_y = top + (bottom - top) // 2
    return (center_x, center_y)

# 下滑函数
def scroll_down():
    """执行一次下滑（滚轮下滑4次，每次500距离）"""
    # 先将鼠标移动到模拟器中心
    center = get_simulator_center()
    pyautogui.moveTo(center[0], center[1])
    time.sleep(0.5)  # 给一点时间让鼠标到位
    
    # 然后执行滚动
    for _ in range(4):
        pyautogui.scroll(-200)  # 负值表示向下滚动
        time.sleep(0.7)  # 短暂停顿避免过快滚动
