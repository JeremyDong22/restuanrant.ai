import collections

# Define Point named tuple to represent coordinates
Point = collections.namedtuple("Point", ["x", "y"])

import pyperclip
import pyautogui
import time

# 基础配置
# 要搜索的城市 - 这个在main/main.py中被设置
search_cities = [
    "重庆",
] # Updated by main/main.py
main_ranking_scroll_times = 9  # 主榜单下滑次数
category_ranking_scroll_times = 3  # 细分品类榜单下滑次数

# 坐标配置 (back_button 将由 Locate.py 定位)
positions = {
    "simulator_top_left": (589, 195),
    "simulator_bottom_right": (883, 833),
    "city_dropdown_button": (632, 246),
    "city_search_box": (679, 254),
    "city_result": (659, 285),
    "food_button": (623, 329),
    "food_ranking_button": (626, 297),
    "category_dropdown": (868, 274),
    "categories": [(695, 336), (762, 328), (829, 331), (627, 363), (694, 372), (769, 371), (835, 369), (631, 403), (688, 405), (766, 404), (829, 407), (640, 444), (689, 437), (766, 441), (823, 440), (631, 476), (694, 477), (768, 476), (840, 477)],
    "back_button": (605, 236)
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
