# Created by AI assistant: Finds JSON in 'data', downloads images into 'image/{note_id}'
# Updated: Changed JSON source to 'data/' and image destination to 'image/{note_id}/'. Removed brand dependency.
# Updated: Fixed path resolution to be relative to script location.

import os
import json
import requests
from pathlib import Path
from urllib.parse import urlparse

# --- Define base directories relative to the script location ---
s_dir = Path(__file__).parent.resolve() # Get the directory where the script is located
DATA_DIR = s_dir / "data"
IMAGE_DIR = s_dir / "image"
# --- End Define base directories ---

def download_images_from_json(json_file_path):
    """
    Parses a JSON file from the data directory, extracts image URLs,
    and downloads them into the corresponding image directory structure.

    Args:
        json_file_path (Path): The path object to the JSON file within DATA_DIR.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path.name}")
        return
    except FileNotFoundError:
        # This check is less likely now as we glob first, but good practice
        print(f"Error: File not found {json_file_path.name}")
        return
    except Exception as e:
        print(f"Error reading {json_file_path.name}: {e}")
        return

    # Extract brand name from filename (relative to DATA_DIR)
    # brand_name = json_file_path.stem # No longer needed for path structure

    for item in data:
        note_id = item.get('note_id')
        images_str = item.get('images')

        if not note_id or not images_str:
            print(f"Warning: Missing 'note_id' or 'images' in an item within {json_file_path.name}")
            continue

        image_urls = [url.strip() for url in images_str.split(',') if url.strip()]

        if not image_urls:
            print(f"Warning: No image URLs found for note_id {note_id} in {json_file_path.name}")
            continue

        # Create directory structure: image/note_id
        # The base IMAGE_DIR is prepended here
        save_dir = IMAGE_DIR / note_id # Removed brand_name
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory {save_dir}: {e}")
            continue # Skip this note if directory creation fails

        print(f"Processing note_id: {note_id} (from {json_file_path.name})") # Removed brand_name from log

        for i, img_url in enumerate(image_urls):
            # Determine image extension or default to jpg
            parsed_url = urlparse(img_url)
            file_ext = os.path.splitext(parsed_url.path)[1].lower()
            if file_ext not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                file_ext = '.jpg' # Default if no common extension found
            image_filename = f"image{i + 1}{file_ext}" # Use detected or default extension

            image_save_path = save_dir / image_filename

            # Skip download if file already exists
            if image_save_path.exists():
                print(f"  Skipping {image_filename}, already exists.")
                continue

            try:
                # Added headers to mimic a browser request slightly more
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(img_url, stream=True, timeout=20, headers=headers) # Increased timeout
                response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)

                with open(image_save_path, 'wb') as img_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        img_file.write(chunk)
                print(f"  Downloaded {image_filename}")

            except requests.exceptions.RequestException as e:
                print(f"  Error downloading {img_url}: {e}")
            except Exception as e:
                print(f"  An unexpected error occurred while downloading {img_url}: {e}")


def find_and_process_json_files():
    """
    Finds all JSON files in the DATA_DIR and processes them.
    """
    if not DATA_DIR.is_dir():
        print(f"Error: Data directory '{DATA_DIR}' not found.")
        print("Please ensure the crawler has run and created the data directory.")
        return

    json_files = list(DATA_DIR.glob('*.json'))

    if not json_files:
        print(f"No JSON files found in directory: {DATA_DIR}")
        return

    print(f"Found {len(json_files)} JSON files in {DATA_DIR}.")

    # Ensure the base image directory exists
    try:
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Ensured base image directory exists: {IMAGE_DIR}")
    except OSError as e:
        print(f"Error creating base image directory {IMAGE_DIR}: {e}")
        return # Stop if base image directory cannot be created

    for json_file in json_files:
        # Skip potential cookies file if it ends up in data dir
        if json_file.name.lower() == 'cookies.json':
             continue
        print(f"--- Processing {json_file.name} ---")
        download_images_from_json(json_file) # Pass the Path object
        print(f"--- Finished processing {json_file.name} ---")

if __name__ == "__main__":
    # Ensure the requests library is installed
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found.")
        print("Please install it using: pip install requests")
        exit(1) # Exit if requests is not installed

    # No need to pass directory, function now uses constants
    find_and_process_json_files()
    print("\nImage download process completed.") 