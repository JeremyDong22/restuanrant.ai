import os
import json
import sys
import re
from supabase import create_client, Client
from dotenv import load_dotenv
import traceback
from collections import defaultdict
from datetime import datetime

# Load environment variables from the root .env file
script_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(script_dir, '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get Supabase credentials from the root .env file
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# 检查API密钥是否存在
if not supabase_url or not supabase_key:
    print("错误: 未找到Supabase凭据。请在 .env 文件中添加 SUPABASE_URL 和 SUPABASE_KEY (文件应位于 dzdp_crawler 目录中)")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Required fields that must be present in each record
REQUIRED_FIELDS = ["榜单", "品牌"]

def extract_city_from_path(file_path):
    """从文件路径中提取城市名称"""
    # 解析文件路径获取目录名
    dir_path = os.path.dirname(file_path)
    
    # 提取目录名中的城市名称（格式如："分析结果文件/上海_20250408_032249"）
    dir_name = os.path.basename(dir_path)
    
    # 使用正则表达式提取城市名称（匹配下划线前的内容）
    city_match = re.match(r'([^_]+)_', dir_name)
    if city_match:
        return city_match.group(1)
    
    # 如果无法解析，返回"未知"
    return "未知"

def rename_brand_name(records):
    """
    重置品牌名的值，基于店铺名称更准确地提取品牌
    - 如果店铺名称包含"·"、"（"或"("，则品牌名为这些字符前面的部分
    - 如果不包含这些字符，则品牌名等于店铺名称
    """
    renamed_count = 0
    for record in records:
        if "店铺名称" in record:
            shop_name = record["店铺名称"]
            old_brand = record.get("品牌", "")
            
            # 尝试提取品牌名
            new_brand = shop_name
            
            # 检查是否包含分隔符并提取前面部分
            for delimiter in ["·", "（", "("]:
                if delimiter in shop_name:
                    new_brand = shop_name.split(delimiter)[0].strip()
                    break
            
            # 更新品牌名（如果有变化）
            if new_brand != old_brand:
                record["品牌"] = new_brand
                renamed_count += 1
                print(f"  更新品牌: '{old_brand}' → '{new_brand}'")
    
    if renamed_count > 0:
        print(f"  总共更新了 {renamed_count} 个品牌名")
    return records

def rename_bangdan(records, filename):
    """
    对于主榜单.json文件，将所有记录的"榜单"字段设置为"主榜单"
    """
    if filename == "主榜单.json":
        changed_count = 0
        for record in records:
            if record.get("榜单") != "主榜单":
                record["榜单"] = "主榜单"
                changed_count += 1
        
        if changed_count > 0:
            print(f"  已将 {changed_count} 条记录的榜单名称修改为'主榜单'")
    
    return records

def validate_data(data):
    """Validate if data meets requirements for upload"""
    if not data or not isinstance(data, list):
        raise ValueError("Data must be a non-empty list")
    
    # Check each record for required fields
    for record in data:
        for field in REQUIRED_FIELDS:
            if field not in record or not record[field]:
                raise ValueError(f"Missing required field: {field}")
    
    return True

def handle_duplicate_keys(data):
    """Handle duplicate primary key combinations"""
    # Keep track of seen (榜单, 品牌, create_date) combinations
    seen_keys = defaultdict(int)
    modified_data = []
    
    for record in data:
        key = (record["榜单"], record["品牌"], record["create_date"])
        seen_keys[key] += 1
        
        # If this is a duplicate, append a counter to make it unique
        if seen_keys[key] > 1:
            new_record = record.copy()
            new_record["品牌"] = f"{record['品牌']}_{seen_keys[key]}"
            modified_data.append(new_record)
            print(f"  Renamed duplicate key: {record['品牌']} → {new_record['品牌']}")
        else:
            modified_data.append(record)
    
    return modified_data

def handle_missing_required_fields(data):
    """处理缺失必要字段的记录"""
    valid_records = []
    skipped_count = 0
    
    for record in data:
        is_valid = True
        for field in REQUIRED_FIELDS:
            if field not in record or not record[field]:
                is_valid = False
                skipped_count += 1
                break
                
        if is_valid:
            valid_records.append(record)
    
    if skipped_count > 0:
        print(f"  警告: 跳过了 {skipped_count} 条缺少必要字段的记录")
        
    return valid_records

def process_json_file(file_path):
    # Get filename without extension to replace "榜单" field
    filename = os.path.basename(file_path)
    filename_without_ext = os.path.splitext(filename)[0]
    
    # 从文件路径提取城市
    city = extract_city_from_path(file_path)
    print(f"  城市: {city}")
    
    # 获取当前日期，格式为YYYY-MM-DD
    current_date = datetime.now().strftime('%Y-%m-%d')
    print(f"  数据采集日期: {current_date}")
    
    # Read JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validate data format
    if not data or not isinstance(data, list):
        raise ValueError(f"Invalid JSON format in {filename}: Must be a non-empty list")
    
    # 处理缺失必要字段的记录
    data = handle_missing_required_fields(data)
    
    # Process each record in the JSON file
    for record in data:
        if not isinstance(record, dict):
            raise ValueError(f"Invalid record format in {filename}: Each item must be an object")
        
        # Replace "榜单" field with filename
        record["榜单"] = filename_without_ext
        
        # 添加城市字段
        record["城市"] = city
        
        # 添加创建日期字段
        record["create_date"] = current_date
    
    # 重命名主榜单
    data = rename_bangdan(data, filename)
    
    # 重置品牌名
    data = rename_brand_name(data)
    
    # Handle potential duplicate keys
    data = handle_duplicate_keys(data)
    
    return data

def upload_to_supabase(data):
    try:
        # Validate data before uploading
        validate_data(data)
        
        # Print first record for debugging
        if data:
            print(f"Sample record: {json.dumps(data[0], ensure_ascii=False)}")
        
        # Upload data to Supabase - use lowercase table name
        result = supabase.table("dzdpdata").upsert(data).execute()
        return result
    except Exception as e:
        # Capture and re-raise with more details
        error_details = f"Error type: {type(e).__name__}, Message: {repr(e)}"
        print(f"Supabase upload error: {error_details}")
        traceback.print_exc()  # Print the full stack trace
        raise Exception(error_details)

def process_directory(directory_path):
    """Processes all JSON files within a given city's results directory."""
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        return 0 # Return 0 processed records
    
    # Keep track of total records processed for this directory
    total_records_in_dir = 0
    total_files_in_dir = 0
    successful_files_in_dir = 0
    failed_files_in_dir = 0
    
    print(f"Processing JSON files in: {directory_path}")
    # Process all JSON files in the directory
    for root, _, files in os.walk(directory_path):
        # We only care about JSON files directly in this directory, not subdirs
        if root == directory_path:
            for file in files:
                if file.endswith('.json') and not file.startswith('.'):  # Skip hidden files
                    file_path = os.path.join(root, file)
                    print(f"Processing file: {file_path}...")
                    total_files_in_dir += 1
                    try:
                        # Process JSON file and get modified data
                        data = process_json_file(file_path)
                        
                        # Upload to Supabase
                        result = upload_to_supabase(data)
                        
                        if data: # Only count if data was successfully processed and not empty
                           num_records = len(data)
                           total_records_in_dir += num_records
                           successful_files_in_dir += 1
                           print(f"Successfully uploaded {num_records} records from {file}")
                        else:
                           print(f"Skipped upload for {file} (no valid data after processing)")
                           failed_files_in_dir += 1
                           
                    except ValueError as ve:
                        # Catch specific data validation/format errors from process_json_file
                        failed_files_in_dir += 1
                        print(f"Skipping file {file} due to data error: {ve}")
                    except Exception as e:
                        failed_files_in_dir += 1
                        print(f"Error processing/uploading {file}: {repr(e)}")
                        # Optionally print traceback for deeper debugging
                        # traceback.print_exc()
                        
    print(f"Finished processing directory: {directory_path}")
    print(f"  Summary: {total_files_in_dir} files found, {successful_files_in_dir} uploaded, {failed_files_in_dir} failed/skipped, {total_records_in_dir} records total.")
    return total_records_in_dir # Return total records uploaded from this directory


def main():
    # Reverted by AI: Look for directories in the same level as the script
    print("Starting Dianping Data Upload Script...")
    script_dir = os.path.dirname(__file__)
    analysis_root = os.path.join(script_dir, "分析结果文件") # Use current dir

    print(f"Looking for analysis results in: {analysis_root}")

    if not os.path.exists(analysis_root):
        print(f"Error: Analysis results directory '{analysis_root}' not found.")
        print("Please ensure dzdp_crawler/Analyzer.py has run and created city folders with JSON files inside.")
        sys.exit(1)

    # Find all city-timestamp folders in the analysis results directory
    city_folders_to_process = []
    for item in os.listdir(analysis_root):
        item_path = os.path.join(analysis_root, item)
        # Basic check for directory and expected naming pattern (e.g., City_YYYYMMDD_HHMMSS)
        if os.path.isdir(item_path) and '_' in item:
            city_folders_to_process.append(item_path)
    
    if not city_folders_to_process:
        print(f"No processed city folders found in '{analysis_root}' to upload.")
        sys.exit(0)
    
    print(f"Found {len(city_folders_to_process)} processed city folders to upload from:")
    for folder in city_folders_to_process:
        print(f"  - {folder}")
        
    grand_total_records = 0
    # Process each found city folder
    for city_folder_path in city_folders_to_process:
        print(f"\n===== Uploading data from City Folder: {os.path.basename(city_folder_path)} =====")
        records_uploaded = process_directory(city_folder_path)
        grand_total_records += records_uploaded
    
    print(f"\n===== Upload Complete. Processed {len(city_folders_to_process)} city folders. =====")
    print(f"Grand total records uploaded across all folders: {grand_total_records}")


if __name__ == "__main__":
    main() 