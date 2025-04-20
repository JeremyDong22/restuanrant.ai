import os
import json
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv, find_dotenv
import sys
import time
import re

# Load environment variables from the root .env file
script_dir = os.path.dirname(__file__)  # Get the directory containing analyzer.py
dotenv_path = os.path.join(script_dir, '..', '.env') # Go up one level to the root directory
load_dotenv(dotenv_path=dotenv_path) # Load the environment variables

# Get the Gemini API key from the root .env file
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    # Add instructions on where the .env file should be
    raise ValueError("GEMINI_API_KEY not found in environment variables. Ensure a .env file exists in the dzdp_crawler directory with this key.")

# 清理API密钥（移除可能的空格或换行符）
gemini_api_key = gemini_api_key.strip()

# 配置Gemini API
try:
    # 使用正确的SDK接口
    genai.configure(api_key=gemini_api_key)
    
    # 尝试简单调用测试连接
    models = genai.list_models()
    print("成功连接到Gemini API")
except Exception as e:
    print(f"连接Gemini API失败: {e}")
    print("请检查API密钥是否正确，或尝试重新生成API密钥")
    sys.exit(1)

# 使用Gemini 2.0 Flash-Lite模型
try:
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    print(f"成功加载模型 gemini-2.0-flash-lite")
except Exception as e:
    print(f"加载模型失败: {e}")
    print("尝试使用备用模型...")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("成功加载备用模型 gemini-1.5-flash")
    except Exception as e2:
        print(f"加载备用模型也失败: {e2}")
        sys.exit(1)

# 分析提示词
PROMPT = """帮我识别这些店铺所在的榜单（一个橙色高亮的文字。一般在"大众点评榜单"的正下方的栏目里面，以菜系或者食物种类命名），
排名（店铺卡片左上角的灰色部分，储存为int，如1，2，3，4，5，6，7，8，9，10），
店铺名称，
品牌（被包含在店铺名称里面，是"·"之前的，如果没有点就是"（"之前的），
评分（含一位小数点的数字），
位置，
细分榜单（在位置的右边一个空格的地方），
价格（在"¥"后面，"人"之前，储存为int）。
以json数组的形式返回给我。"""

# 自然排序函数
def natural_sort_key(s):
    """提取数字用于自然排序"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def process_folder(folder_path):
    """处理文件夹中的所有图片并一次性发送到Gemini API"""
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return []
    
    # 获取文件夹中的所有图片文件
    image_files = [f for f in os.listdir(folder_path) if f.endswith('.png') or f.endswith('.jpg')]
    image_files.sort(key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else -1)
    
    if not image_files:
        print(f"文件夹中没有图片: {folder_path}")
        return []
    
    # 加载所有图片
    images = []
    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)
        try:
            img = Image.open(image_path)
            # 检查图片是否有效
            img.verify()  # 验证图片完整性
            # 重新打开，因为verify会消耗图片对象
            img = Image.open(image_path)
            images.append(img)
            print(f"已加载图片: {image_path}")
        except Exception as e:
            print(f"加载图片 {image_path} 时出错: {e}")
    
    if not images:
        print("没有成功加载任何图片")
        return []
    
    # 构建请求内容
    content_parts = [PROMPT]
    content_parts.extend(images)
    
    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 一次性发送所有图片进行分析
            print(f"正在发送 {len(images)} 张图片到Gemini API进行分析... (尝试 {attempt+1}/{max_retries})")
            
            # 使用正确的API调用方式
            response = model.generate_content(content_parts)
            
            # 检查响应是否有效
            if response.text and len(response.text) > 0:
                print("分析完成，正在处理结果...")
                return extract_json_from_response(response.text)
            else:
                print(f"API返回空响应 (尝试 {attempt+1}/{max_retries})")
                if attempt < max_retries - 1:
                    print("等待2秒后重试...")
                    time.sleep(2)
                    continue
        except Exception as e:
            print(f"API调用出错 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("等待3秒后重试...")
                time.sleep(3)
                continue
    
    print(f"在 {max_retries} 次尝试后仍无法成功调用API，跳过当前文件夹")
    return []

def extract_json_from_response(response_text):
    """从Gemini的响应中提取JSON数据"""
    try:
        # 尝试找到JSON数组的开始和结束
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx != 0:
            json_text = response_text[start_idx:end_idx]
            # 解析JSON
            data = json.loads(json_text)
            return data
        else:
            print(f"无法在响应中找到JSON数组: {response_text}")
            return []
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"响应文本: {response_text}")
        return []

def determine_json_filename(data):
    """根据JSON数据确定输出文件名"""
    if not data:
        return "未知榜单.json"
    
    # 获取第一条数据的榜单名称
    first_item = data[0]
    banner_name = first_item.get("榜单", "未知榜单")
    
    return f"{banner_name}.json"

def save_results(data, output_folder, ranking_type):
    """保存JSON结果到文件"""
    if not data:
        print(f"没有数据需要保存: {ranking_type}")
        return

    # Filter data based on ranking type
    if ranking_type == "主榜单":
        data = data[:30]
        print(f"已筛选主榜单数据，保留前 30 条")
    elif ranking_type.startswith("细分榜单"):
        data = data[:10]
        print(f"已筛选 {ranking_type} 数据，保留前 10 条")

    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 确定输出文件名
    if ranking_type == "主榜单":
        output_filename = "主榜单.json"
    else:
        output_filename = determine_json_filename(data)
    
    # 保存JSON文件
    output_path = os.path.join(output_folder, output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"结果已保存到: {output_path}")

def process_folder_for_analysis(input_folder):
    """Processes subfolders ('主榜单', '细分榜单*') within a specific city's results folder."""
    if not os.path.exists(input_folder):
        print(f"Input folder does not exist: {input_folder}")
        return
    
    # Construct output path relative to the script directory
    script_dir = os.path.dirname(__file__)
    analysis_root = os.path.join(script_dir, "分析结果文件")
    city_output_folder = os.path.join(analysis_root, os.path.basename(input_folder))
    if not os.path.exists(city_output_folder):
        os.makedirs(city_output_folder)
        print(f"Created output folder: {city_output_folder}")
    
    folder_count = 0
    
    # Process Main Ranking
    main_ranking_folder = os.path.join(input_folder, "主榜单")
    if os.path.exists(main_ranking_folder):
        print(f"\nProcessing Main Ranking: {main_ranking_folder}")
        main_ranking_results = process_folder(main_ranking_folder) # process_folder calls Gemini
        save_results(main_ranking_results, city_output_folder, "主榜单")
        folder_count += 1
    else:
        print(f"Main Ranking folder not found: {main_ranking_folder}")

    # Process Category Rankings (sorted naturally)
    subdirectories = []
    try:
        for item in os.listdir(input_folder):
            item_path = os.path.join(input_folder, item)
            if os.path.isdir(item_path) and item.startswith("细分榜单"):
                subdirectories.append(item)
    except FileNotFoundError:
        print(f"Error listing directory {input_folder}")
        return # Skip this city folder if listing fails

    subdirectories.sort(key=natural_sort_key)
    print(f"Found {len(subdirectories)} category ranking folders to process.")

    for item in subdirectories:
        item_path = os.path.join(input_folder, item)
        print(f"\nProcessing Category Ranking: {item_path}")
        category_results = process_folder(item_path) # process_folder calls Gemini
        # Pass item name (e.g., "细分榜单1") to save_results to determine filename
        save_results(category_results, city_output_folder, item)
        folder_count += 1
    
    print(f"\nFinished processing {folder_count} subfolders in {input_folder}.")


def main():
    # Reverted by AI: Look for directories in the same level as the script
    print("Starting Dianping Screenshot Analyzer...")
    script_dir = os.path.dirname(__file__)
    screenshot_root = os.path.join(script_dir, "搜索结果截图") # Use current dir
    analysis_root = os.path.join(script_dir, "分析结果文件")    # Use current dir

    print(f"Looking for screenshots in: {screenshot_root}")
    print(f"Saving analysis results to: {analysis_root}")

    if not os.path.exists(screenshot_root):
        print(f"Error: Screenshot directory '{screenshot_root}' not found.")
        print("Please ensure dzdp_crawler/Search.py has run and created city folders inside.")
        sys.exit(1)
    
    if not os.path.exists(analysis_root):
        print(f"Creating analysis output directory: {analysis_root}")
        os.makedirs(analysis_root)

    # Find all city-timestamp folders in the screenshot directory
    city_folders_to_process = []
    for item in os.listdir(screenshot_root):
        item_path = os.path.join(screenshot_root, item)
        # Basic check for directory and expected naming pattern (e.g., City_YYYYMMDD_HHMMSS)
        if os.path.isdir(item_path) and '_' in item:
            city_folders_to_process.append(item_path)
    
    if not city_folders_to_process:
        print(f"No city folders found in '{screenshot_root}' to analyze.")
        sys.exit(0)
    
    print(f"Found {len(city_folders_to_process)} city folders to analyze:")
    for folder in city_folders_to_process:
        print(f"  - {folder}")
        
    total_processed = 0
    # Process each found city folder
    for city_folder_path in city_folders_to_process:
        print(f"\n===== Analyzing City Folder: {os.path.basename(city_folder_path)} =====")
        process_folder_for_analysis(city_folder_path)
        total_processed += 1
    
    print(f"\n===== Analysis Complete. Processed {total_processed} city folders. =====")
    print(f"JSON results saved in subdirectories under '{analysis_root}'.")


if __name__ == "__main__":
    main() 