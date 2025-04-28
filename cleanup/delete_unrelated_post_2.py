# Created by AI assistant.
# This script deletes posts from the Supabase 'posts' table 
# where the 'is related' column is False.
# WARNING: This performs a destructive delete operation.

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import argparse

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment variables.")

# Initialize Supabase client
supabase: Client = create_client(url, key)

# Table configuration
TABLE_NAME = 'posts'
IS_RELATED_COLUMN = 'is related'  # Column name with space

def delete_unrelated_posts(dry_run=False):
    """
    Deletes posts from the specified table where the IS_RELATED_COLUMN is False.

    Args:
        dry_run (bool): If True, only counts the posts to be deleted without actually deleting them.
    """
    print(f"Connecting to Supabase table: {TABLE_NAME}")

    try:
        # First, count how many posts match the criteria
        # Need to use the string 'false' for the filter
        count_response = supabase.table(TABLE_NAME)\
                                 .select("*", count='exact')\
                                 .eq(IS_RELATED_COLUMN, 'false')\
                                 .execute()

        if count_response.count is None:
             print("Could not retrieve count of unrelated posts. Maybe an RLS issue or incorrect column name?")
             return

        count = count_response.count
        print(f"Found {count} posts marked as unrelated ('{IS_RELATED_COLUMN}' is False).")

        if count == 0:
            print("No unrelated posts found to delete.")
            return

        if dry_run:
            print("Dry run enabled. No posts will be deleted.")
            return

        # Confirm deletion with the user
        confirm = input(f"Are you sure you want to delete these {count} posts? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled.")
            return

        print(f"Proceeding with deletion of {count} posts...")
        # Perform the deletion
        # Supabase delete with eq filter handles the deletion in batches if needed
        delete_response = supabase.table(TABLE_NAME)\
                                  .delete()\
                                  .eq(IS_RELATED_COLUMN, 'false')\
                                  .execute()
        
        # Check the response - delete() often returns the deleted items if SELECT RLS is granted
        if hasattr(delete_response, 'data') and delete_response.data:
             deleted_count = len(delete_response.data)
             print(f"Successfully deleted {deleted_count} posts.")
             if deleted_count < count:
                  print(f"Warning: Expected to delete {count} posts, but only {deleted_count} were reported deleted. Possible RLS issue?")
        else:
             # If data isn't returned (e.g., stricter RLS), we can't confirm the exact count deleted easily
             print(f"Delete operation sent. Supabase reported success, but couldn't confirm the exact count of deleted rows (this might be due to RLS). Please verify in your database.")
             # You might want to re-run the count query here to verify

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Delete posts marked as unrelated to food.')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Count posts to be deleted without actually deleting them.'
    )
    args = parser.parse_args()

    delete_unrelated_posts(dry_run=args.dry_run) 