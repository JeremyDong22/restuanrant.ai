# cleanup_storage.py
# Script to identify and delete folders in a Supabase Storage bucket
# that do not correspond to a post_id in the 'posts' table.
# Removed redundant/empty loop causing IndentationError.
# Added by AI assistant.

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Configuration ---
BUCKET_NAME = "xhs_image"  # Replace with your actual bucket name if different
# --- End Configuration ---

def list_all_folders(supabase: Client, bucket: str) -> set[str]:
    """Lists all 'folders' (prefixes) at the root level of the bucket."""
    print(f"Listing folders in bucket '{bucket}'...")
    folders = set()
    try:
        # Initial check if bucket seems empty at the root
        all_objects = supabase.storage.from_(bucket).list() # Lists top-level files/folders

        if not all_objects:
            print("No objects or folders found at the root.")
            return folders

        # The previous simpler approach (commented out or removed) was less reliable.
        # Using the method below which lists all objects.

        # ---- MOST RELIABLE METHOD ----
        # List ALL objects and derive folders from prefixes. This handles nested objects.
        # Note: This can be resource-intensive for very large buckets.
        print("Fetching all object paths to determine folders...")
        all_objects_paginated = []
        offset = 0
        limit = 1000 # Max limit per Supabase docs
        while True:
            page = supabase.storage.from_(bucket).list(options={"limit": limit, "offset": offset})
            if not page:
                break
            all_objects_paginated.extend(page)
            if len(page) < limit:
                break
            offset += limit
            print(f"Fetched {len(all_objects_paginated)} objects so far...")

        folders.clear() # Reset folders set
        for obj in all_objects_paginated:
            name = obj.get('name')
            if name and '/' in name:
                folder_name = name.split('/')[0]
                folders.add(folder_name)
            # If an object is directly in the root and looks like a folder name (e.g., UUID)
            elif name and '.' not in name and '/' not in name:
                 # Let's assume root objects without '.' are folders if posts table uses such IDs.
                 # Check if it looks like a potential post_id (e.g., numeric or UUID)
                 if name.isdigit() or len(name) > 10: # Basic check for numeric or UUID-like ID
                    folders.add(name)


        print(f"Found {len(folders)} potential folders.")
        # print(f"Folders found: {folders}") # Uncomment for debugging
        return folders

    except Exception as e:
        print(f"Error listing folders in bucket '{bucket}': {e}")
        return set()

def get_all_post_ids(supabase: Client) -> set[str]:
    """Fetches all post_id values from the posts table."""
    print("Fetching all post_ids from 'posts' table...")
    post_ids = set()
    try:
        # Paginate through results if necessary
        current_page = 0
        page_size = 1000 # Adjust page size as needed
        while True:
            range_start = current_page * page_size
            range_end = range_start + page_size - 1
            response = supabase.table('posts').select('post_id').range(range_start, range_end).execute()

            if hasattr(response, 'data') and response.data:
                fetched_ids = {str(item['post_id']) for item in response.data if item.get('post_id') is not None}
                post_ids.update(fetched_ids)
                if len(response.data) < page_size:
                    break # Last page
                current_page += 1
            else:
                # Handle potential API error structure or empty response
                if hasattr(response, 'error') and response.error:
                     print(f"Error fetching post_ids: {response.error}")
                elif not hasattr(response, 'data'):
                     print(f"Unexpected response structure: {response}")
                break # Exit loop if no data or error

        print(f"Found {len(post_ids)} unique post_ids.")
        # print(f"Post IDs: {post_ids}") # Uncomment for debugging
        return post_ids
    except Exception as e:
        print(f"Error fetching post_ids: {e}")
        return set()

def delete_folder(supabase: Client, bucket: str, folder_name: str):
    """Deletes all objects within a given folder prefix."""
    print(f"Attempting to delete folder '{folder_name}'...")
    try:
        # List all objects within the folder prefix
        files_to_delete_response = supabase.storage.from_(bucket).list(path=folder_name)

        if files_to_delete_response:
            file_paths = [f"{folder_name}/{file['name']}" for file in files_to_delete_response]
            if not file_paths:
                print(f"No files found in folder '{folder_name}'. Skipping deletion.")
                # Optionally delete the potentially empty folder marker if one exists
                # supabase.storage.from_(bucket).remove([f"{folder_name}/"]) # Check if this works
                return

            print(f"Deleting {len(file_paths)} files from folder '{folder_name}'...")
            # print(f"Files: {file_paths}") # Uncomment for debugging
            remove_response = supabase.storage.from_(bucket).remove(file_paths)

            # Check response for errors
            # Note: supabase-py remove operation might not return detailed errors per file in data
            # It often returns the list of successfully deleted items. Check for absence of errors.
            if hasattr(remove_response, 'error') and remove_response.error:
                 print(f"Error deleting files in folder '{folder_name}': {remove_response.error}")
            # Check if data indicates success (e.g., contains deleted items)
            elif hasattr(remove_response, 'data') and remove_response.data:
                 print(f"Successfully deleted files for folder '{folder_name}'.")
                 # If Supabase doesn't auto-delete empty prefixes, we might need an extra step if required.
            else:
                 # If response is unexpected or empty without error, log it.
                 print(f"Deletion response for folder '{folder_name}' might indicate issues or no files deleted: {remove_response}")

        else:
            print(f"Could not list files in folder '{folder_name}' or folder is empty. Skipping deletion.")
            # Handle potential errors during list operation if not caught earlier

    except Exception as e:
        print(f"An exception occurred while deleting folder '{folder_name}': {e}")


def main():
    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file or environment variables.")
        sys.exit(1)

    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase client initialized.")
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        sys.exit(1)

    storage_folders = list_all_folders(supabase, BUCKET_NAME)
    if not storage_folders:
        print("Could not retrieve folders from storage or bucket is empty.")
        # Decide whether to exit or continue
        # sys.exit(1) # Exit if folders are mandatory

    db_post_ids = get_all_post_ids(supabase)
    if not db_post_ids:
        print("Could not retrieve post_ids from database or table is empty.")
        # Decide whether to exit or continue
        # sys.exit(1) # Exit if post_ids are mandatory for comparison

    # Find folders in storage that are NOT in the database post_ids
    orphaned_folders = storage_folders - db_post_ids

    if not orphaned_folders:
        print("No orphaned folders found. Storage is clean.")
    else:
        print(f"Found {len(orphaned_folders)} orphaned folders to delete: {orphaned_folders}")
        # Confirmation step (optional but recommended)
        confirm = input("Proceed with deleting these folders? (yes/no): ").lower()
        if confirm == 'yes':
            print("Starting deletion...")
            for folder in orphaned_folders:
                delete_folder(supabase, BUCKET_NAME, folder)
            print("Deletion process complete.")
        else:
            print("Deletion cancelled by user.")

if __name__ == "__main__":
    main() 