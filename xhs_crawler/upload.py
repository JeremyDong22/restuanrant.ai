# upload.py
# Script to upload scraped Xiaohongshu data from the 'data' directory to Supabase 'posts' and 'post_brand' tables.
# Handles duplicates by checking existing post_ids in 'posts'.
# Generates image URLs based on post_id: https://.../xhs_image/{post_id}/image{index}.jpg
# Corrected data directory path to be relative to the script location.
# Added exit(1) if brand_id_map fails to load to prevent inconsistent state.
# Added .strip() to brand name mapping and lookup to handle potential whitespace issues.
# Implemented pagination for fetching brand map to handle >1000 brands.

import os
import json
import glob
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm
import re
from pathlib import Path
from urllib.parse import quote
import math # For ceiling batches

# --- Constants ---
SUPABASE_STORAGE_BASE_URL = "https://wdpeoyugsxqnpwwtkqsl.supabase.co/storage/v1/object/public"
IMAGE_BUCKET_NAME = "xhs_image"
BRAND_TABLE_NAME = "brand"
POSTS_TABLE_NAME = "posts" # Target table for posts
POST_BRAND_TABLE_NAME = "post_brand" # Target table for relations
BATCH_SIZE = 100 # Records per batch insert
# --- End Constants ---

# Load environment variables from the parent directory
script_dir = os.path.dirname(__file__)
# Adjust path to go up one level from 'xhs_crawler' to the project root
dotenv_path = os.path.join(script_dir, '..', '.env')
print(f"Attempting to load .env file from: {dotenv_path}")
if not os.path.exists(dotenv_path):
    print(f"Warning: .env file not found at {dotenv_path}. Trying script directory.")
    # fallback to script directory if not found in parent
    dotenv_path_alt = os.path.join(script_dir, '.env')
    if os.path.exists(dotenv_path_alt):
        dotenv_path = dotenv_path_alt
        print(f"Found .env file in script directory: {dotenv_path}")
    else:
         print("Warning: .env file not found in parent or script directory.")
         # Decide how to handle this - raise error or continue if defaults are set elsewhere
         # For now, let load_dotenv handle potential failure if no file is found

load_dotenv(dotenv_path=dotenv_path)


# Get Supabase credentials from environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY") # Use ANON key for table operations

# Check if credentials are loaded
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL or ANON KEY not found in .env file. Ensure it's in the project root or script directory.")

# Create Supabase client
try:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Supabase client created successfully.")
except Exception as e:
    print(f"Error creating Supabase client: {e}")
    exit(1)

def get_brand_id_map():
    """Fetches ALL brand names and IDs from Supabase using pagination and returns a case-insensitive mapping."""
    brand_map = {}
    page_size = 1000 # Supabase default limit
    current_page = 0
    total_fetched = 0
    print(f"Fetching ALL brand data from table: {BRAND_TABLE_NAME} using pagination (page size: {page_size})...")

    try:
        while True:
            start_index = current_page * page_size
            end_index = start_index + page_size - 1
            # print(f"Fetching brand page {current_page + 1} (range: {start_index}-{end_index})...")
            response = supabase.table(BRAND_TABLE_NAME).select("brand_id, name", count='exact').range(start_index, end_index).execute()

            if response.data:
                for brand in response.data:
                    # Map lowercased stripped name to brand_id for case-insensitive lookup
                    if brand.get('name'): # Ensure name exists
                        brand_map[brand['name'].strip().lower()] = brand['brand_id']
                    else:
                        print(f"Warning: Found brand record (page {current_page + 1}) with missing name in database.")
                total_fetched += len(response.data)
                # Check if it was the last page
                if len(response.data) < page_size or (response.count is not None and total_fetched >= response.count):
                    break
                current_page += 1
            else:
                 # Handle case where no data is returned on a page or error occurs
                 if hasattr(response, 'error') and response.error:
                     print(f"API Error fetching brand page {current_page + 1}: {response.error}")
                     # Decide whether to break or continue, depending on severity
                     # For now, break to avoid partial map
                     raise Exception(f"Failed to fetch all brands due to API error: {response.error}")
                 else:
                     # No more data found
                     break # Exit loop if no data and no error

        print(f"Successfully fetched {total_fetched} brands in total ({len(brand_map)} unique names mapped).")

    except Exception as e:
        print(f"Error fetching brand data from Supabase: {e}")
        # Exit if the brand map cannot be reliably fetched
        print("Critical error: Cannot proceed without complete brand ID mapping. Exiting.")
        exit(1) # Stop the script
    return brand_map

def get_existing_post_ids():
    """Fetches all existing post_ids from the posts table."""
    existing_ids = set()
    try:
        print(f"Fetching existing post_ids from table: {POSTS_TABLE_NAME}...")
        # Fetch all post_ids - consider pagination for very large tables
        current_page = 0
        page_size = 1000 # Supabase default limit
        while True:
            response = supabase.table(POSTS_TABLE_NAME).select("post_id", count='exact').range(current_page * page_size, (current_page + 1) * page_size - 1).execute()
            if response.data:
                 for post in response.data:
                      existing_ids.add(post['post_id'])
                 # Check if we fetched less than the page size, meaning it's the last page
                 if len(response.data) < page_size or response.count is not None and len(existing_ids) >= response.count:
                     break
                 current_page += 1
            else:
                 # No more data or an error occurred
                 if hasattr(response, 'error') and response.error:
                      print(f"Error fetching existing post_ids (page {current_page}): {response.error}")
                 break # Stop fetching if no data or error

        print(f"Successfully fetched {len(existing_ids)} existing post_ids.")
    except Exception as e:
        print(f"Error fetching existing post_ids from Supabase: {e}")
        print("Warning: Proceeding without checking for duplicates. Duplicate posts might be inserted if script is re-run.")
        # Return empty set to avoid blocking uploads, but duplicates are possible
    return existing_ids

def load_json_file(file_path):
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {file_path} is not a valid JSON file")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def format_publish_date(date_str):
    """Format the publish date string into YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Check for MM-DD format (e.g., "04-15")
    match = re.fullmatch(r"(\d{1,2})-(\d{1,2})", date_str.strip())
    if match:
        month, day = match.groups()
        current_year = datetime.now().year
        # Format correctly with leading zeros if needed
        try:
            # Validate date components before formatting
            formatted_date = datetime(current_year, int(month), int(day)).strftime("%Y-%m-%d")
            return formatted_date
        except ValueError:
             print(f"Warning: Invalid date components in MM-DD format: {date_str}")
             return None
    
    # Check if it's already in YYYY-MM-DD format
    match_ymd = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", date_str.strip())
    if match_ymd:
         try:
              # Validate date components before returning
              year, month, day = match_ymd.groups()
              datetime(int(year), int(month), int(day)) # Check if valid date
              return date_str.strip()
         except ValueError:
              print(f"Warning: Invalid date components in YYYY-MM-DD format: {date_str}")
              return None
              
    # Handle relative dates like "昨天", "前天" (Could be expanded)
    if "昨天" in date_str:
         # This requires knowing the 'create_date' ideally, difficult here
         # For simplicity, return None or approximate
         return None 
    
    # Add more specific date parsing if other formats exist (e.g., using dateutil library)
    
    # If format is unknown or unparseable, return None
    print(f"Warning: Unrecognized publish_date format: '{date_str}'")
    return None

def process_and_upload_posts(data, brand_id_map, existing_post_ids):
    """
    Processes records from JSON, filters duplicates, prepares data for 'posts' and 'post_brand',
    and uploads them to Supabase tables.
    """
    if not data:
        print("No data provided for processing.")
        return 0, 0 # Return counts for posts and relations uploaded

    if brand_id_map is None:
        print("Warning: Brand ID map is not available. Cannot create post_brand relations.")
        brand_id_map = {} # Use an empty map to avoid errors later

    posts_to_insert = []
    posts_to_update = [] # 新增：存储需要更新的已有帖子
    post_brand_relations_to_insert = []
    processed_count = 0
    skipped_duplicates = 0
    update_count = 0 # 新增：记录更新的帖子数量

    print("Processing records: filtering duplicates, formatting data, generating image URLs...")
    for record in tqdm(data, desc="Processing records"):
        processed_count += 1
        post_id = record.get("post_id")

        if not post_id:
            print(f"Warning: Record missing post_id. Skipping: {record.get('title', 'N/A')}")
            continue

        # --- Deduplication Check (Only for posts, not for brand relations) ---
        is_duplicate = post_id in existing_post_ids
        if is_duplicate:
            skipped_duplicates += 1
            # 记录这是一个重复帖子，但继续处理以处理潜在的新品牌关联和更新动态信息
        # --- End Deduplication Check ---

        # --- Prepare Post Data ---
        formatted_publish_date = format_publish_date(record.get("publish_date"))

        # Generate Image URLs based on  post_id
        original_images_str = record.get("images", "")
        supabase_image_urls = []
        if original_images_str:
            try:
                # Assuming images are comma-separated URLs or paths
                original_urls = [url.strip() for url in original_images_str.split(',') if url.strip()]
                for i, _ in enumerate(original_urls):
                    image_filename = f"image{i + 1}.jpg"
                    # URL-encode components safely
                    safe_post_id = quote(str(post_id))
                    safe_image_filename = quote(image_filename)
                    # Construct the Supabase public URL path
                    supabase_path = f"{SUPABASE_STORAGE_BASE_URL}/{IMAGE_BUCKET_NAME}/{safe_post_id}/{safe_image_filename}"
                    supabase_image_urls.append(supabase_path)
            except Exception as img_e:
                 print(f"Warning: Error processing image string for post {post_id}: '{original_images_str}'. Error: {img_e}")
                 supabase_image_urls = [] # Reset on error

        # Handle potential missing keys gracefully, defaulting to None or 0
        post_payload = {
            "post_id": post_id,
            "likes": int(record.get("likes", 0)) if record.get("likes") is not None else None,
            "title": record.get("title"),
            "author": record.get("author"),
            "publish_date": formatted_publish_date,
            "content": record.get("content"),
            "images": supabase_image_urls, # Store as a list for TEXT[]
            "collections": int(record.get("collections", 0)) if record.get("collections") is not None else None,
            "comments": int(record.get("comments", 0)) if record.get("comments") is not None else None,
        }
        
        # 新增：为已存在的帖子创建简化的更新载荷（只包含动态变化的数据）
        if is_duplicate:
            update_payload = {
                "post_id": post_id, # 主键，用于匹配
                "likes": int(record.get("likes", 0)) if record.get("likes") is not None else None,
                "collections": int(record.get("collections", 0)) if record.get("collections") is not None else None,
                "comments": int(record.get("comments", 0)) if record.get("comments") is not None else None,
            }
            posts_to_update.append(update_payload)
            update_count += 1
        else:
            # 新帖子完整插入
            posts_to_insert.append(post_payload)
        # --- End Prepare Post Data ---

        # --- Prepare Post-Brand Relation Data ---
        # 不管帖子是否存在，都处理品牌关联
        brand_name = record.get("brand")
        if brand_name:
            # Use lowercased stripped key for lookup
            lookup_key = brand_name.strip().lower()
            brand_id = brand_id_map.get(lookup_key)
            if brand_id:
                post_brand_payload = {
                    "post_id": post_id, # Matches posts.post_id
                    "brand_id": brand_id # Matches brand.brand_id
                }
                post_brand_relations_to_insert.append(post_brand_payload)
                if is_duplicate:
                    print(f"Note: Creating new brand relation for existing post {post_id} with brand '{brand_name}' (ID: {brand_id})")
            else:
                # Use lookup_key (lower, stripped) in warning message for clarity
                print(f"Warning: Brand ID not found for brand '{lookup_key}' (original: '{brand_name}') in record with post_id '{post_id}'. No post_brand relation created.")
        # --- End Prepare Post-Brand Relation Data ---

    print(f"Processing complete. Found {len(posts_to_insert)} new posts to insert and {update_count} existing posts to update.")
    print(f"Skipped {skipped_duplicates} duplicates (but will update their dynamic data).")
    print(f"Created {len(post_brand_relations_to_insert)} post-brand relations (including relations for existing posts).")

    # --- Batch Upload Posts ---
    total_posts = len(posts_to_insert)
    uploaded_posts_count = 0
    failed_posts = []
    if total_posts > 0:
        print(f"Uploading {total_posts} new records to Supabase table '{POSTS_TABLE_NAME}'...")
        num_batches = math.ceil(total_posts / BATCH_SIZE)
        for i in tqdm(range(num_batches), desc=f"Uploading post batches"):
            batch = posts_to_insert[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
            try:
                # Use insert, as duplicates are pre-filtered
                result = supabase.table(POSTS_TABLE_NAME).insert(batch).execute()
                # Basic check (response structure might vary)
                if result.data:
                    uploaded_posts_count += len(result.data)
                # Check for errors if the client provides them
                elif hasattr(result, 'error') and result.error:
                    print(f"API Error uploading post batch {i + 1}/{num_batches}: {result.error}")
                    failed_posts.extend(batch)
            except Exception as e:
                print(f"Exception uploading post batch {i + 1}/{num_batches}: {e}")
                failed_posts.extend(batch)
        print(f"Uploaded {uploaded_posts_count} posts successfully.")
        if failed_posts:
            print(f"Failed to upload {len(failed_posts)} posts.")
            # Optionally save failed records
            # with open("failed_post_uploads.json", 'w', encoding='utf-8') as f:
            #     json.dump(failed_posts, f, ensure_ascii=False, indent=4)

    # --- Update Existing Posts (Dynamic Data) ---
    # 新增：更新已有帖子的动态信息
    total_updates = len(posts_to_update)
    updated_posts_count = 0
    failed_updates = []
    if total_updates > 0:
        print(f"Updating {total_updates} existing records in Supabase table '{POSTS_TABLE_NAME}'...")
        num_batches = math.ceil(total_updates / BATCH_SIZE)
        for i in tqdm(range(num_batches), desc=f"Updating post batches"):
            batch = posts_to_update[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
            try:
                for post in batch:
                    post_id = post.get('post_id')
                    if post_id:
                        # 使用update而非upsert，因为我们确定记录已存在
                        update_data = {k: v for k, v in post.items() if k != 'post_id'}
                        result = supabase.table(POSTS_TABLE_NAME).update(update_data).eq('post_id', post_id).execute()
                        if result.data:
                            updated_posts_count += len(result.data)
                        elif hasattr(result, 'error') and result.error:
                            print(f"API Error updating post {post_id}: {result.error}")
                            failed_updates.append(post)
            except Exception as e:
                print(f"Exception updating post batch {i + 1}/{num_batches}: {e}")
                failed_updates.append(batch)
        print(f"Updated {updated_posts_count} existing posts successfully.")
        if failed_updates:
            print(f"Failed to update {len(failed_updates)} posts.")
            
    # --- Batch Upload Post-Brand Relations ---
    total_relations = len(post_brand_relations_to_insert)
    uploaded_relations_count = 0
    failed_relations = []
    if total_relations > 0:
        print(f"Upserting {total_relations} post-brand relations to Supabase table '{POST_BRAND_TABLE_NAME}'...")
        num_batches = math.ceil(total_relations / BATCH_SIZE)
        for i in tqdm(range(num_batches), desc=f"Upserting relation batches"):
            batch = post_brand_relations_to_insert[i*BATCH_SIZE:(i+1)*BATCH_SIZE]
            try:
                # Use upsert for relations to handle potential reruns gracefully
                result = supabase.table(POST_BRAND_TABLE_NAME).upsert(batch, on_conflict='post_id,brand_id').execute()
                if result.data:
                     uploaded_relations_count += len(result.data)
                elif hasattr(result, 'error') and result.error:
                     # Ignore pk violation errors if using upsert, could be other errors
                     if 'duplicate key value violates unique constraint' not in str(result.error):
                          print(f"API Error upserting relation batch {i + 1}/{num_batches}: {result.error}")
                          failed_relations.extend(batch)

            except Exception as e:
                print(f"Exception upserting relation batch {i + 1}/{num_batches}: {e}")
                failed_relations.extend(batch)
        print(f"Upserted {uploaded_relations_count} post-brand relations successfully.")
        if failed_relations:
            print(f"Failed to upsert {len(failed_relations)} relations.")
            # Optionally save failed records
            # with open("failed_relation_uploads.json", 'w', encoding='utf-8') as f:
            #     json.dump(failed_relations, f, ensure_ascii=False, indent=4)

    return uploaded_posts_count + updated_posts_count, uploaded_relations_count

def main():
    """Main function to find JSON files, fetch mappings/existing IDs, process, and upload data."""

    # --- Fetch Brand ID Map ---
    brand_id_map = get_brand_id_map()
    # No longer exit if map fails, just warn, as posts can still be uploaded

    # --- Fetch Existing Post IDs for Deduplication ---
    existing_post_ids = get_existing_post_ids()

    # Correctly define data_dir relative to the script location
    script_dir = os.path.dirname(__file__)
    data_dir = Path(script_dir) / "data"
    if not data_dir.is_dir():
        print(f"Error: 'data' directory not found at {data_dir.resolve()}")
        print("Please ensure the crawler has run and created the 'data' directory with JSON files.")
        return

    # Find all JSON files within the 'data' directory
    json_files_generator = data_dir.glob("*.json")
    # Convert generator to list for easier handling and filtering
    json_files = [str(f) for f in json_files_generator if f.name != 'cookies.json']

    if not json_files:
        print(f"No JSON data files found in the '{data_dir}' directory (excluding cookies.json).")
        return

    print(f"Found {len(json_files)} JSON files in '{data_dir}' to process: {json_files}")

    # Process each file
    total_uploaded_posts = 0
    total_uploaded_relations = 0
    for file_path in tqdm(json_files, desc="Processing files"):
        print(f"\nProcessing {file_path}...")
        data = load_json_file(file_path)
        if data:
            # Pass maps and existing IDs to the processing function
            posts_count, relations_count = process_and_upload_posts(data, brand_id_map, existing_post_ids)
            total_uploaded_posts += posts_count
            total_uploaded_relations += relations_count
            # Add newly uploaded post IDs to the set to prevent duplicates *within the same run*
            # if processing multiple files that might contain the same new post.
            if posts_count > 0:
                 newly_added_ids = {post['post_id'] for post in data if post.get('post_id') and post['post_id'] not in existing_post_ids}
                 existing_post_ids.update(newly_added_ids)


    print(f"\nUpload complete.")
    print(f"Total new posts uploaded across all files: {total_uploaded_posts}")
    print(f"Total post-brand relations upserted across all files: {total_uploaded_relations}")


if __name__ == "__main__":
    main() 