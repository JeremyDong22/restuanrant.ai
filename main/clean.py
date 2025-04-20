# Created by AI assistant.
# main/clean.py
# Cleans up temporary data directories used by the crawlers.

import os
import shutil
import sys

# Define paths relative to this script's location
SCRIPT_DIR = os.path.dirname(__file__)
DZDP_SCREENSHOT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'dzdp_crawler', '搜索结果截图'))
DZDP_ANALYSIS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'dzdp_crawler', '分析结果文件'))
XHS_IMAGE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'xhs_crawler', 'image'))
XHS_DATA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'xhs_crawler', 'data'))

DIRS_TO_CLEAN = [
    DZDP_SCREENSHOT_DIR,
    DZDP_ANALYSIS_DIR,
    XHS_IMAGE_DIR,
    XHS_DATA_DIR,
]

def clean_directory(dir_path):
    """Removes all files and subdirectories within a given directory, then recreates the directory."""
    if not os.path.exists(dir_path):
        print(f"Directory not found, skipping cleanup: {dir_path}")
        return
    
    if not os.path.isdir(dir_path):
        print(f"Error: Path is not a directory, skipping cleanup: {dir_path}")
        return

    try:
        print(f"Cleaning directory: {dir_path} ...")
        # Remove the entire directory tree
        shutil.rmtree(dir_path)
        # Recreate the directory
        os.makedirs(dir_path)
        print(f"Successfully cleaned and recreated: {dir_path}")
    except Exception as e:
        print(f"Error cleaning directory {dir_path}: {e}")
        # Attempt to recreate directory even if rmtree failed partially
        if not os.path.exists(dir_path):
            try:
                 os.makedirs(dir_path)
                 print(f"Recreated directory after error: {dir_path}")
            except Exception as e2:
                 print(f"Could not recreate directory after error: {dir_path}: {e2}")

def main():
    print("Starting cleanup process...")
    print("This will REMOVE ALL content within the following directories:")
    for dir_path in DIRS_TO_CLEAN:
        print(f"  - {dir_path}")
    
    for dir_path in DIRS_TO_CLEAN:
        clean_directory(dir_path)
    print("\nCleanup finished.")

if __name__ == "__main__":
    main() 