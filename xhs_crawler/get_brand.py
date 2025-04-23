# Created by AI assistant.
# xhs_crawler/get_brand.py
# Moved from main/get_brand.py to xhs_crawler/get_brand.py.
# Fixed import of main/config.py to correctly access SELECTED_RANKINGS.
# Contains functions to:
# 1. Get a unique list of brands from selected rankings in 'dzdpdata'.
# 2. Update the BRANDS list in xhs_crawler/config.py.

import os
import sys
import traceback # Keep for error handling
from dotenv import load_dotenv
from supabase import create_client, Client
import re # For apply_to_xhs_config

# Import config from main directory - use absolute path to ensure correct import
main_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main'))
sys.path.insert(0, main_dir)  # Insert at beginning of path to ensure it's found first
try:
    import config as main_config
    print(f"Successfully imported main config from {main_dir}")
    print(f"Available rankings: {main_config.SELECTED_RANKINGS if hasattr(main_config, 'SELECTED_RANKINGS') else 'SELECTED_RANKINGS not found'}")
except ImportError as e:
    print(f"Error importing main config: {e}")
    sys.exit(1)

# --- Supabase Client Initialization ---
def get_supabase_client():
    """Initializes and returns the Supabase client."""
    # Load environment variables from the root .env file
    script_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(script_dir, '..', '.env')
    load_dotenv(dotenv_path=dotenv_path)

    supabase_url = os.getenv("SUPABASE_URL")
    # Use ANON key here as we only need read access for dzdpdata and write to config file
    supabase_key = os.getenv("SUPABASE_KEY") # Or use a specific read-only key if preferred

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


def get_selected_brands():
    """Gets unique brand names from dzdpdata based on SELECTED_RANKINGS in main/config.py
       and the most recent create_date in the dzdpdata table."""
    print("\n--- Getting Selected Brands for XHS (Latest Date) --- ")
    
    # Ensure SELECTED_RANKINGS exists in main_config
    if not hasattr(main_config, 'SELECTED_RANKINGS'):
        print("Error: SELECTED_RANKINGS not found in main/config.py")
        print("Available attributes in main_config:", dir(main_config))
        return []
        
    selected_rankings = main_config.SELECTED_RANKINGS
    if not selected_rankings:
        print("Warning: No rankings specified in main/config.py. Returning empty list.")
        return []
    
    try:
        # 1. Find the most recent create_date in the dzdpdata table
        print("Finding the most recent create_date in dzdpdata...")
        date_response = supabase.table("dzdpdata").select("create_date").order("create_date", desc=True).limit(1).execute()
        
        if not date_response.data:
            print("Error: Could not find any create_date in dzdpdata table.")
            return []
            
        most_recent_date = date_response.data[0]['create_date']
        print(f"Most recent create_date found: {most_recent_date}")

        # 2. Fetch brands matching selected rankings AND the most recent date
        print(f"Fetching brands from rankings: {selected_rankings} for date: {most_recent_date}")
        response = supabase.table("dzdpdata")\
                          .select("品牌")\
                          .in_("榜单", selected_rankings)\
                          .eq("create_date", most_recent_date)\
                          .execute()

        if response.data:
            # Extract unique, non-empty brand names
            selected_brands = set(item['品牌'] for item in response.data if item.get('品牌') and str(item.get('品牌')).strip())
            brand_list = sorted(list(selected_brands)) # Sort for consistency
            print(f"Found {len(brand_list)} unique brands for selected rankings on {most_recent_date}.")
            # print(f"Selected Brands: {brand_list}") # Optional: print the list
            return brand_list
        else:
            print(f"No brands found matching the selected rankings for date {most_recent_date}.")
            return []
            
    except Exception as e:
        print(f"Error fetching selected brands: {e}")
        traceback.print_exc()
        return [] # Return empty list on error

def apply_to_xhs_config(brand_list):
    """Updates the BRANDS list in xhs_crawler/config.py with the provided list."""
    print("\n--- Applying Brands to XHS Config --- ")
    if not isinstance(brand_list, list):
        print("Error: Input must be a list of brand names.")
        return False

    xhs_config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    print(f"Target XHS config file: {xhs_config_path}")

    if not os.path.exists(xhs_config_path):
        print(f"Error: XHS config file not found at {xhs_config_path}")
        return False

    try:
        with open(xhs_config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        start_line = -1
        end_line = -1
        in_brands_list = False

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("BRANDS = ["):
                start_line = i
                in_brands_list = True
                # Check if list ends on the same line
                if stripped_line.endswith("]"):
                     end_line = i
                     break
            elif in_brands_list and stripped_line == "]":
                 end_line = i
                 break
            elif in_brands_list and stripped_line.startswith("]"):
                 # Handle cases like "] # comment"
                 end_line = i
                 break

        if start_line != -1 and end_line != -1:
            # Construct the new list string
            # Ensure proper quoting for brand names containing spaces or special chars
            # Also ensure each item ends with a comma for valid Python list syntax
            formatted_brands = [f'    "{brand.replace("\"", "\\\"")}",' # Comma moved outside the f-string
                              for brand in brand_list]
            new_brands_content = "BRANDS = [\n" + '\n'.join(formatted_brands) + "\n]"
            
            # Add comment indicating it was updated
            new_brands_content += " # Updated by xhs_crawler/get_brand.py\n"

            # Replace the old list definition
            new_lines = lines[:start_line] + [new_brands_content] + lines[end_line+1:]

            with open(xhs_config_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Successfully updated BRANDS list in {xhs_config_path} with {len(brand_list)} brands.")
            return True
        else:
            print("Error: Could not find the 'BRANDS = [...] ' list definition in the XHS config file.")
            print("Please check the format of xhs_crawler/config.py.")
            return False
            
    except Exception as e:
        print(f"Error updating XHS config file: {e}")
        traceback.print_exc()
        return False

# --- Main Execution --- 
if __name__ == "__main__":
    print("Running Brand Processing Script (Get & Apply)...")
    
    # Step 1: Get brands from selected rankings
    print("\nStep 1: Getting selected brands...")
    selected_brands = get_selected_brands()
    
    # Step 2: Apply the selected brands to the XHS config
    if selected_brands: # Only apply if we got some brands
        print("\nStep 2: Applying brands to XHS config...")
        success = apply_to_xhs_config(selected_brands)
        if success:
            print("XHS config updated successfully.")
        else:
            print("Failed to update XHS config.")
    else:
        print("\nStep 2: Skipped applying brands to XHS config as no brands were selected.")

    print("\nBrand Processing Script (Get & Apply) finished.") 