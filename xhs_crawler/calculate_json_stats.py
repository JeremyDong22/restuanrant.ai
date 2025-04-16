# calculate_json_stats.py
# Calculates the number of JSON files, the total number of items (posts),
# and the total number of images within a specified alphabetical range
# of filenames in the xhs_crawler/data directory.
# Usage:
# python3 xhs_crawler/calculate_json_stats.py <start_filename_without_extension> <end_filename_without_extension>
# Example:
# python3 xhs_crawler/calculate_json_stats.py "八合里牛肉火锅" "喜茶"

import json
import sys
from pathlib import Path
import os

# Define the data directory relative to this script's location
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"

def calculate_stats(start_filename, end_filename):
    """Calculates and prints the JSON file count, total item count, and total image count within the range."""
    if not DATA_DIR.is_dir():
        print(f"Error: Data directory not found at {DATA_DIR}")
        return

    print(f"Scanning directory: {DATA_DIR}")
    print(f"Calculating stats for files from '{start_filename}.json' to '{end_filename}.json' (inclusive)...")

    file_count = 0
    total_items = 0
    total_images = 0 # Initialize image counter
    start_file_target = start_filename + ".json"
    end_file_target = end_filename + ".json"

    try:
        all_json_files = sorted([f for f in DATA_DIR.iterdir() if f.is_file() and f.suffix == ".json"])
        
        # Filter files alphabetically within the range
        filtered_files = [
            f for f in all_json_files 
            if start_file_target <= f.name <= end_file_target
        ]

        file_count = len(filtered_files)

        if file_count == 0:
            print("No JSON files found within the specified range.")
            return

        print(f"Found {file_count} JSON files in the range. Processing...")

        for file_path in filtered_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        total_items += len(data)
                        # Count images in each item
                        for item in data:
                            # Check if item is a dict and has a non-empty 'images' string
                            if isinstance(item, dict) and 'images' in item and isinstance(item['images'], str) and item['images']:
                                # Split the string by ", " and count the URLs
                                image_urls = item['images'].split(', ')
                                total_images += len(image_urls)
                    else:
                        print(f"Warning: {file_path.name} does not contain a list. Skipping item and image count for this file.")
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {file_path.name}. Skipping item and image count for this file.")
            except Exception as e:
                print(f"Warning: Error reading file {file_path.name}: {e}. Skipping item and image count for this file.")

        print("\n--- Calculation Complete ---")
        print(f"Total JSON files found in range: {file_count}")
        print(f"Total items (posts) found in these files: {total_items}")
        print(f"Total images found in these files: {total_images}") # Print total images

    except Exception as e:
        print(f"An error occurred during processing: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 xhs_crawler/calculate_json_stats.py <start_filename_without_extension> <end_filename_without_extension>")
        print("Example: python3 xhs_crawler/calculate_json_stats.py \"八合里牛肉火锅\" \"喜茶\"")
        sys.exit(1)

    start_name = sys.argv[1]
    end_name = sys.argv[2]

    calculate_stats(start_name, end_name) 