# Updated by AI: Remove brand dependency, use note_id directly for structure.
# image_upload.py
# Uploads images from the local 'image/{note_id}' directory (created by image_download.py)
# to Supabase storage bucket 'xhs_image', using '{note_id}/{filename}' as the storage path.
# Ensures the bucket exists and handles potential existing files.

import os
import mimetypes
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm
from urllib.parse import quote # Keep for note_id and filename encoding

# --- Constants ---
IMAGE_BUCKET_NAME = "xhs_image"
# Define image directory relative to this script's location
SCRIPT_DIR = Path(__file__).parent
LOCAL_IMAGE_DIR = SCRIPT_DIR / "image"
# BRAND_TABLE_NAME = "brand" # Removed brand dependency
# --- End Constants ---

# Load environment variables from the parent directory
script_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(script_dir, '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Get Supabase credentials from the parent directory .env file
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY") # Service key is named SUPABASE_KEY in .env

# Check if credentials are loaded
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL or SERVICE KEY not found in .env file. Ensure SUPABASE_KEY is set.")

# Create Supabase client
try:
    supabase: Client = create_client(supabase_url, supabase_key)
    print("Supabase client created successfully.")
except Exception as e:
    print(f"Error creating Supabase client: {e}")
    exit(1)

def get_mime_type(file_path):
    """Get the MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream' # Default if type unknown

def upload_image(local_path: Path, storage_path: str):
    """Uploads a single image file to Supabase storage."""
    try:
        # Ensure local file exists
        if not local_path.is_file():
            print(f"Error: Local file not found: {local_path}")
            return False

        mime_type = get_mime_type(local_path)
        
        with open(local_path, 'rb') as f:
            # Check if file already exists (optional, basic check)
            try:
                supabase.storage.from_(IMAGE_BUCKET_NAME).get_public_url(storage_path)
                # print(f"Skipping upload: {storage_path} already exists...")
                # return True # Uncomment to skip existing files
            except Exception:
                pass # File likely doesn't exist

            f.seek(0)
            response = supabase.storage.from_(IMAGE_BUCKET_NAME).upload(
                path=storage_path,
                file=f,
                file_options={"content-type": mime_type, "cache-control": "3600"}
            )
            return True # Assume success if no exception

    except Exception as e:
        # Check if the error message indicates the file already exists
        # Supabase specific error might be needed here, e.g., checking for HTTP 409 or specific error codes/messages
        if "The resource already exists" in str(e): # Example check, adjust based on actual Supabase error
             # This primarily catches errors if the check in main() failed unexpectedly
             print(f"Skipping upload (error catch): {storage_path} already exists.")
             return True # Treat as success if already exists
        print(f"Error uploading {local_path} to {storage_path}: {e}")
        return False

def main():
    """Finds images locally in image/{note_id} and uploads them to Supabase storage."""
    # --- Removed brand ID map fetching ---

    if not LOCAL_IMAGE_DIR.is_dir():
        print(f"Error: Local image directory '{LOCAL_IMAGE_DIR}' not found.")
        print("Please ensure the image_download.py script has run and created the image/{note_id} structure.")
        return

    print(f"Scanning for images in: {LOCAL_IMAGE_DIR.resolve()}")

    # Iterate directly through note_id folders
    note_id_folders = [d for d in LOCAL_IMAGE_DIR.iterdir() if d.is_dir()]
    if not note_id_folders:
        print(f"No note_id folders found in {LOCAL_IMAGE_DIR}.")
        return

    total_uploaded = 0
    total_failed = 0
    total_skipped = 0 # Keep track of skipped files

    # Ensure bucket exists (requires service key permissions)
    try:
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(b.name == IMAGE_BUCKET_NAME for b in buckets)
        if not bucket_exists:
            print(f"Bucket '{IMAGE_BUCKET_NAME}' not found. Creating...")
            # Make bucket public by default
            supabase.storage.create_bucket(IMAGE_BUCKET_NAME, options={"public": True})
            print(f"Bucket '{IMAGE_BUCKET_NAME}' created successfully.")
        else:
            print(f"Bucket '{IMAGE_BUCKET_NAME}' already exists.")
    except Exception as e:
        print(f"Error checking or creating bucket '{IMAGE_BUCKET_NAME}': {e}")
        # return # Optionally stop if bucket management fails

    print(f"Starting image upload to bucket: {IMAGE_BUCKET_NAME}")
    # Loop directly through note_id folders
    for note_id_dir in tqdm(note_id_folders, desc="Processing notes"):
        note_id = note_id_dir.name
        # Find all image files, case-insensitive extensions common for images
        image_files = [f for f in note_id_dir.glob('*') if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']]

        for local_image_path in image_files:
            image_filename = local_image_path.name

            # URL-encode components for safety
            # safe_brand_id = quote(str(brand_id)) # Removed brand ID
            safe_note_id = quote(note_id)
            safe_image_filename = quote(image_filename)

            # Construct storage path: {note_id}/{image_filename}
            storage_path = f"{safe_note_id}/{safe_image_filename}"

            # Check if file exists before attempting upload
            try:
                 # Use list() method with search to check existence efficiently
                 existing_files = supabase.storage.from_(IMAGE_BUCKET_NAME).list(path=safe_note_id, options={'search': safe_image_filename})
                 if existing_files:
                     # print(f"Skipping: {storage_path} already exists.")
                     total_skipped += 1
                     continue # Skip to the next file

            except Exception as e:
                 print(f"Warning: Could not check existence for {storage_path}. Error: {e}. Proceeding with upload attempt.")
                 # Decide if you want to stop or log this differently

            # Attempt upload only if existence check passed or failed gracefully
            if upload_image(local_image_path, storage_path):
                total_uploaded += 1
            else:
                # If upload_image returns False, it means an error occurred that wasn't 'already exists'
                # The 'already exists' case within upload_image should return True if caught there
                total_failed += 1

    print(f"\nImage upload process completed.")
    print(f"Successfully uploaded: {total_uploaded}")
    print(f"Skipped (already exist): {total_skipped}") # Report skipped files
    print(f"Failed: {total_failed}")

if __name__ == "__main__":
    main() 