# Created by AI assistant.
# main/refresh.py
# Contains function to refresh the 'brand' table with all unique brands from 'dzdpdata'.

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import traceback

# --- Supabase Client Initialization ---
def get_supabase_client():
    """Initializes and returns the Supabase client."""
    # Load environment variables from the root .env file
    script_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(script_dir, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") # Assumes service key for inserts

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL or Key not found in root .env file")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Supabase client created successfully.")
        return supabase
    except Exception as e:
        print(f"Error creating Supabase client: {e}")
        sys.exit(1)

supabase = get_supabase_client()
# --- End Supabase Client Initialization ---

def refresh_brand_table():
    """Fetches distinct brands from dzdpdata, handling pagination, and inserts new ones into the brand table."""
    print("\n--- Refreshing Brand Table ---")
    try:
        # 1. Get distinct, non-null brand names from dzdpdata, handling pagination
        print("Fetching all distinct brands from dzdpdata (handling pagination)...")
        all_dzdp_brands_data = []
        current_page = 0
        page_size = 1000 # Supabase default limit per request

        while True:
            start_index = current_page * page_size
            end_index = start_index + page_size - 1
            print(f"Fetching brands: rows {start_index} to {end_index}...")
            response = supabase.table("dzdpdata").select("品牌", count='exact').range(start_index, end_index).execute()

            # Check for errors (basic)
            if hasattr(response, 'error') and response.error:
                print(f"Error fetching data page {current_page}: {response.error}")
                # Decide whether to stop or continue based on error type if needed
                break 
                
            if response.data:
                all_dzdp_brands_data.extend(response.data)
            
            # Determine if we've reached the end
            # Check if the number of items returned is less than the page size,
            # or if the total count (if available and reliable) is reached.
            # Using returned data length is generally safer.
            if len(response.data) < page_size:
                 print("Fetched last page of data.")
                 break # Exit loop if last page fetched

            current_page += 1
            # Safety break to prevent infinite loops in unexpected scenarios
            if current_page > 100: # Adjust limit as needed based on expected data size
                print("Warning: Reached maximum page limit (100). Stopping fetch.")
                break
                
        print(f"Total raw brand entries fetched: {len(all_dzdp_brands_data)}")

        if not all_dzdp_brands_data:
            print("No brands found in dzdpdata table after fetching all pages.")
            return

        # Extract unique, non-empty brand names from the *complete* dataset
        dzdp_brands = set(item['品牌'] for item in all_dzdp_brands_data if item.get('品牌') and str(item.get('品牌')).strip()) # Also ensure not just whitespace
        print(f"Found {len(dzdp_brands)} unique, non-empty brands in dzdpdata after processing all pages.")

        if not dzdp_brands:
            print("No valid brand names extracted from dzdpdata.")
            return

        # 2. Get existing brand names from the brand table
        print("Fetching existing brands from brand table...")
        existing_brands_response = supabase.table("brand").select("name").execute()
        existing_brands = set(item['name'] for item in existing_brands_response.data)
        print(f"Found {len(existing_brands)} existing brands.")

        # 3. Determine which brands are new
        new_brands = dzdp_brands - existing_brands
        print(f"Found {len(new_brands)} new brands to insert.")

        # 4. Insert new brands into the brand table
        if new_brands:
            records_to_insert = [{'name': brand_name} for brand_name in new_brands]
            print(f"Inserting new brands: {list(new_brands)[:10]}...") # Print first few
            insert_response = supabase.table("brand").insert(records_to_insert).execute()
            
            # Basic check on response (might need adjustment based on actual response)
            if hasattr(insert_response, 'data') and insert_response.data: 
                print(f"Successfully inserted {len(insert_response.data)} new brands.")
            elif hasattr(insert_response, 'error') and insert_response.error:
                 print(f"Error inserting brands: {insert_response.error}")
            else:
                 # Handle cases where insertion might have partially succeeded or failed silently
                 print("Insertion completed. Verify results in Supabase.")
        else:
            print("No new brands to insert.")

        print("Brand table refresh process finished.")

    except Exception as e:
        print(f"Error during brand table refresh: {e}")
        traceback.print_exc()

# --- Main Execution --- 
if __name__ == "__main__":
    print("Running Brand Table Refresh Script...")
    refresh_brand_table()
    print("\nBrand Table Refresh Script finished.") 