# Updated by AI assistant: Pass raw image bytes directly to Supabase upload.
# Updated by AI assistant: Corrected the environment variable name in the error message.
# Created by AI assistant: Combines JSON parsing and direct Supabase upload.
# Reads JSON files from 'data/', downloads image URLs found within,
# and directly uploads the image data to Supabase Storage without saving locally.
# Configuration for Supabase (URL, Key, Bucket) is loaded from a .env file.
# Optimization: Checks Supabase for existing images before downloading.
# Update: Changed .env file path loading to script's directory.
# Update: Corrected error message for missing env vars.

import os
import json
import requests
import io
from pathlib import Path
from urllib.parse import urlparse, quote
from supabase import create_client, Client
from dotenv import load_dotenv
import time

# --- Define base directories relative to the script location ---
s_dir = Path(__file__).parent.resolve() # Get the directory where the script is located
DATA_DIR = s_dir / "data"
# --- End Define base directories ---

# --- Load Supabase Configuration ---
# Load environment variables from the parent directory .env file (not the script's directory)
p_dir = s_dir.parent.resolve()
load_dotenv(dotenv_path=p_dir / '.env')

# Get Supabase credentials from the parent directory .env file
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # Use Service Key for backend operations
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET_NAME")

supabase: Client = None # Initialize Supabase client later
# --- End Supabase Configuration ---

# --- MIME Type Helper ---
def get_mime_type(extension):
    """Returns a best-guess MIME type for common image extensions."""
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
    }
    return mime_map.get(extension.lower(), 'application/octet-stream') # Default if unknown
# --- End MIME Type Helper ---


def upload_image_to_supabase(note_id, img_url, index):
    """
    Downloads an image from a URL into memory and uploads it to Supabase Storage.

    Args:
        note_id (str): The note ID, used for structuring the path in Supabase.
        img_url (str): The URL of the image to download.
        index (int): The index of the image for this note_id (for naming).

    Returns:
        bool: True if upload was successful or skipped, False otherwise.
    """
    global supabase # Use the globally initialized client

    if not supabase or not SUPABASE_BUCKET:
        print("  Error: Supabase client or bucket not configured.")
        return False

    try:
        # Determine image extension or default to jpg
        parsed_url = urlparse(img_url)
        file_ext = os.path.splitext(parsed_url.path)[1].lower()
        if not file_ext or file_ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            file_ext = '.jpg' # Default if no common or valid extension found

        # Use quote to handle special characters in filenames for URL paths
        image_filename_base = f"image{index + 1}"
        image_filename = f"{image_filename_base}{file_ext}"
        # Ensure the filename is URL-safe for Supabase path
        safe_image_filename = quote(image_filename)

        supabase_path = f"{note_id}/{safe_image_filename}"

        # --- Download image into memory ---
        print(f"  Attempting to download: {img_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(img_url, stream=True, timeout=30, headers=headers) # Increased timeout
        response.raise_for_status() # Raises HTTPError for bad responses

        image_data = response.content # Read image data into memory
        # --- End Download ---

        # --- Upload to Supabase ---
        print(f"  Uploading {image_filename} to Supabase path: {supabase_path}")
        mime_type = get_mime_type(file_ext)

        # Check if file exists in Supabase before uploading - This check is now done earlier at the note_id level
        # We still use upsert=false here as a fallback or for partial uploads, but the primary check is above.
        try:
            # Pass the raw image bytes directly to the upload function
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=supabase_path,
                file=image_data, # Pass the raw bytes directly
                file_options={"content-type": mime_type, "cache-control": "3600", "upsert": "false"}
            )
            # print(f"  Successfully uploaded {image_filename}") # Less verbose success message below
            return True
        except Exception as upload_error:
            # Check if the error is because the file already exists
            if 'duplicate key value violates unique constraint' in str(upload_error) or 'The resource already exists' in str(upload_error) or 'already exists' in str(upload_error).lower():
                 # This case should be less frequent now due to the note_id check, but kept as safety
                 print(f"  Skipping {image_filename}, already exists in Supabase at {supabase_path}.")
                 return True # Treat as success because the file is there
            else:
                print(f"  Error uploading {image_filename} to Supabase: {upload_error}")
                return False
        # --- End Upload ---

    except requests.exceptions.RequestException as e:
        print(f"  Error downloading {img_url}: {e}")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred processing {img_url}: {e}")
        return False


def process_json_file(json_file_path):
    """
    Parses a JSON file, extracts image URLs, checks Supabase for existing images,
    and triggers their direct upload if they don't exist.

    Args:
        json_file_path (Path): The path object to the JSON file within DATA_DIR.
    """
    global supabase # Use the globally initialized client
    if not supabase or not SUPABASE_BUCKET:
        print("Error: Supabase client or bucket not configured during processing.")
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path.name}")
        return
    except FileNotFoundError:
        print(f"Error: File not found {json_file_path.name}")
        return
    except Exception as e:
        print(f"Error reading {json_file_path.name}: {e}")
        return

    for item in data:
        note_id = item.get('note_id')
        images_str = item.get('images')

        if not note_id or not images_str:
            print(f"Warning: Missing 'note_id' or 'images' in an item within {json_file_path.name}")
            continue

        image_urls = [url.strip() for url in images_str.split(',') if url.strip()]
        expected_image_count = len(image_urls)

        if not image_urls:
            print(f"Warning: No image URLs found for note_id {note_id} in {json_file_path.name}")
            continue

        print(f"Processing note_id: {note_id} (from {json_file_path.name}) - Expecting {expected_image_count} images.")

        # --- Check Supabase first ---
        try:
            existing_files = supabase.storage.from_(SUPABASE_BUCKET).list(path=note_id)
            # Filter out potential placeholder objects if storage creates them for empty folders
            # Supabase list() might return a placeholder - check specifics if needed
            # A simple check is len(existing_files) > 0 if the folder itself exists
            actual_file_count = len([f for f in existing_files if f.get('id') is not None]) # Count actual files

            if actual_file_count >= expected_image_count:
                print(f"  Skipping note_id {note_id}: Found {actual_file_count} existing files in Supabase (expected {expected_image_count}).")
                continue # Skip to the next item in the JSON
            else:
                print(f"  Found {actual_file_count} existing files in Supabase for note_id {note_id}. Proceeding with upload check.")

        except Exception as list_error:
            # If listing fails (e.g., RLS issues, bucket not found), log error and proceed cautiously
            # Or decide to stop if this check is critical
            print(f"  Warning: Could not list files for note_id {note_id} in Supabase: {list_error}. Proceeding without skip check.")
            # Fall through to process images individually
        # --- End Check Supabase ---

        success_count = 0
        fail_count = 0

        for i, img_url in enumerate(image_urls):
            # Add a small delay to avoid overwhelming the source server or Supabase
            time.sleep(0.1) # 100ms delay between downloads/uploads

            # upload_image_to_supabase now handles the final check/skip via upsert=false
            # but the main skip logic is the note_id check above.
            if upload_image_to_supabase(note_id, img_url, i):
                success_count += 1
            else:
                fail_count += 1

        print(f"  Finished processing note_id {note_id}. Success/Skipped: {success_count}, Failed: {fail_count}")


def find_and_process_json_files():
    """
    Finds all JSON files in the DATA_DIR and processes them for direct upload.
    """
    global supabase # Ensure we use the global client

    if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_BUCKET:
        # Corrected the variable name in the error message below
        print("Error: Supabase environment variables (SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET_NAME) not set.")
        # Corrected error message to reflect actual loading location
        print(f"Please ensure they are defined in the .env file located in the parent directory ({p_dir}) or as system environment variables.")
        return

    # Initialize Supabase client
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection by listing buckets (optional, but good check)
        # This might require storage admin privileges depending on RLS
        # supabase.storage.list_buckets()
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        return

    if not DATA_DIR.is_dir():
        print(f"Error: Data directory '{DATA_DIR}' not found.")
        print("Please ensure the crawler has run and created the data directory.")
        return

    json_files = list(DATA_DIR.glob('*.json'))

    if not json_files:
        print(f"No JSON files found in directory: {DATA_DIR}")
        return

    print(f"Found {len(json_files)} JSON files in {DATA_DIR}.")

    total_start_time = time.time()
    for json_file in json_files:
        file_start_time = time.time()
        # Skip potential cookies file
        if json_file.name.lower() == 'cookies.json':
             print(f"Skipping {json_file.name}")
             continue
        print(f"--- Processing {json_file.name} ---")
        process_json_file(json_file) # Pass the Path object
        file_end_time = time.time()
        print(f"--- Finished processing {json_file.name} in {file_end_time - file_start_time:.2f} seconds ---")

    total_end_time = time.time()
    print(f"\nImage direct upload process completed in {total_end_time - total_start_time:.2f} seconds.")


if __name__ == "__main__":
    # Check essential libraries
    try:
        import requests
        import supabase
        import dotenv
    except ImportError as e:
        print(f"Error: Missing required library - {e.name}")
        print("Please install requirements: pip install requests supabase python-dotenv")
        exit(1)

    find_and_process_json_files() 