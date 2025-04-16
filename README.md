# Created by AI assistant. Contains overview, features, structure, workflow, setup, usage, configuration, and dependencies for the project.

# Dianping & Xiaohongshu Crawling and Analysis Pipeline

## Overview

This project provides an automated pipeline for scraping data from Dianping (大众点评) and Xiaohongshu (小红书) based on specific brands and locations. It extracts ranking information, post details, and images, processes them, and uploads the results to a Supabase database. The pipeline consists of two main crawler modules (`dzdp_crawler`, `xhs_crawler`) orchestrated by a central controller (`main/main.py`).

-   **Dianping Crawler (`dzdp_crawler`):** Uses GUI automation (PyAutoGUI) to interact with an Android emulator or mirrored device to navigate Dianping, capture ranking screenshots, analyze them using Gemini Vision API, and upload structured data to Supabase.
-   **Xiaohongshu Crawler (`xhs_crawler`):** Uses Playwright to automate browser interaction with Xiaohongshu, search for posts related to specific brands (derived from Dianping data), scrape post details and image URLs, download/upload images to Supabase Storage, and upload post metadata to Supabase.
-   **Main Controller (`main`):** Manages the overall workflow, updates configurations, refreshes brand lists, and executes the crawler modules in sequence.

## Features

-   **Multi-Platform Crawling:** Scrapes data from both Dianping and Xiaohongshu.
-   **GUI Automation (Dianping):** Uses PyAutoGUI for interacting with an emulator/device interface.
    -   Initial interactive setup (`Locate.py`) to record screen coordinates.
    -   Automated city selection, navigation to food rankings, and screenshot capture.
-   **Web Automation (Xiaohongshu):** Uses Playwright for browser automation.
    -   Persistent browser session management (`openbrowser.py`).
    -   Cookie handling for login (`get_cookie.py`, `config.py`).
    -   Brand-based search, filtering (most likes), and infinite scrolling.
-   **Image Analysis (Dianping):** Leverages Google Gemini Vision API (`Analyzer.py`) to extract structured data (ranking, brand, shop name, rating, price, etc.) from screenshots.
-   **Data Management:**
    -   Uploads structured data (Dianping rankings, XHS posts) to Supabase tables.
    -   Uploads images (from XHS) to Supabase Storage, linking them to posts.
    -   Handles data cleaning, deduplication, and relationship mapping (posts to brands).
    -   Dynamically updates the list of brands for XHS crawling based on recent Dianping data (`refresh.py`, `get_brand.py`).
-   **Automated Pipeline:** Orchestrated by `main/main.py` for sequential execution of tasks.
-   **Configuration:** Centralized configuration for cities, rankings, automation flags (`main/config.py`), API keys, and database credentials (`.env`).
-   **Temporary Data Cleanup:** Script (`main/clean.py`) to remove intermediate files (screenshots, analysis results, downloaded images).

## Project Structure

```
.
├── .env                  # Environment variables (API keys, Supabase creds) - GITIGNORED
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── browser_data/         # Playwright persistent context data - GITIGNORED
├── dzdp_crawler/         # Dianping Crawler Module
│   ├── .git/             # Submodule git data (if applicable) - GITIGNORED
│   ├── .gitignore        # DZDP specific gitignore
│   ├── Config.py         # DZDP configuration (coordinates, scroll times)
│   ├── Locate.py         # Script to locate GUI elements via user input
│   ├── Search.py         # Script to automate searching and screenshotting on DZDP
│   ├── Analyzer.py       # Script to analyze screenshots using Gemini API
│   ├── Upload.py         # Script to upload analyzed DZDP data to Supabase
│   ├── __pycache__/      # Python cache - GITIGNORED
│   ├── 分析结果文件/     # Directory for JSON results from Analyzer.py - GITIGNORED
│   └── 搜索结果截图/     # Directory for screenshots from Search.py - GITIGNORED
├── main/                 # Main Pipeline Controller Module
│   ├── config.py         # Main pipeline configuration (cities, rankings, automation flags)
│   ├── main.py           # Main script to orchestrate the pipeline
│   ├── refresh.py        # Script to refresh the 'brand' table in Supabase
│   ├── get_brand.py      # Script to get selected brands and update xhs_crawler config
│   ├── clean.py          # Script to clean up temporary directories
│   └── __pycache__/      # Python cache - GITIGNORED
├── 搜索结果截图/         # Empty placeholder? - GITIGNORED
└── xhs_crawler/          # Xiaohongshu Crawler Module
    ├── .gitignore        # XHS specific gitignore
    ├── config.py         # XHS configuration (brands list, like threshold, cookie handling)
    ├── get_cookie.py     # Script to manually log in and save XHS cookie
    ├── openbrowser.py    # Script to manage a persistent Playwright browser instance
    ├── crawler.py        # Main XHS crawler script (Playwright automation)
    ├── image_download.py # Script to download images locally (optional, can be skipped)
    ├── image_upload.py   # Script to upload locally downloaded images to Supabase (optional)
    ├── image_direct_upload.py # Script to download and upload images directly to Supabase
    ├── upload.py         # Script to upload scraped XHS post data to Supabase
    ├── calculate_json_stats.py # Utility script to count items in data files
    ├── __pycache__/      # Python cache - GITIGNORED
    ├── data/             # Directory for scraped XHS JSON data - GITIGNORED
    └── image/            # Directory for downloaded XHS images - GITIGNORED

```
*(Directories marked GITIGNORED are excluded from version control as defined in `.gitignore`)*

## Workflow

```mermaid
graph TD
    subgraph Preparation [Module 1: Preparation]
        direction TB
        P1[Load Emulator/Mirror] --> P2{Relocate Emulator?};
        P2 -- Yes --> P3[Run dzdp_crawler/Locate.py];
        P2 -- No --> P4[Skip Relocation];
        P3 --> P5{Automate XHS Login?};
        P4 --> P5;
        P5 -- Yes --> P6{Get New Cookie?};
        P5 -- No --> P10[Skip XHS Login Steps];
        P6 -- Yes --> P7[Run xhs_crawler/get_cookie.py];
        P6 -- No --> P8[Skip Cookie Acquisition];
        P7 --> P8;
        P8 --> P9{Open New Browser?};
        P9 -- Yes --> P11[Run xhs_crawler/openbrowser.py (background)];
        P9 -- No --> P12[Skip Open Browser];
        P10 --> EndPrep[Preparation Complete];
        P11 --> EndPrep;
        P12 --> EndPrep;
    end

    subgraph DZDP [Module 2: Dianping Crawling]
        direction TB
        DZ1[Update DZDP Cities (main/main.py)] --> DZ2[Run dzdp_crawler/Search.py];
        DZ2 --> DZ3[Run dzdp_crawler/Analyzer.py];
        DZ3 --> DZ4[Run dzdp_crawler/Upload.py];
        DZ4 --> EndDZDP[DZDP Complete];
    end

    subgraph XHS [Module 3: Xiaohongshu Crawling]
        direction TB
        XHS1[Run main/refresh.py (Update Supabase 'brand' table)] --> XHS2[Run main/get_brand.py (Update xhs_crawler/config.py)];
        XHS2 --> XHS3[Run xhs_crawler/crawler.py (Scrape Posts)];
        XHS3 --> XHS4[Run xhs_crawler/image_direct_upload.py (Upload Images)];
        XHS4 --> XHS5[Run xhs_crawler/upload.py (Upload Post Data)];
        XHS5 --> EndXHS[XHS Complete];
    end

     subgraph Cleanup [Module 4: Cleanup]
         direction TB
         C1{Perform Cleanup?} --> C2[Run main/clean.py];
         C1 -- No --> EndCleanup[Cleanup Skipped];
         C2 --> EndCleanup[Cleanup Complete];
     end

    Start[Start main/main.py] --> Preparation;
    Preparation --> DZDP;
    DZDP --> XHS;
    XHS --> Cleanup;
    Cleanup --> End[Pipeline Finish];

    style Preparation fill:#f9f,stroke:#333,stroke-width:2px
    style DZDP fill:#ccf,stroke:#333,stroke-width:2px
    style XHS fill:#cfc,stroke:#333,stroke-width:2px
    style Cleanup fill:#fcc,stroke:#333,stroke-width:2px

```

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install Dependencies:** Make sure you have Python 3 installed.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The user running the script mentioned having `python3` instead of `python`. Adjust commands accordingly if needed.*

3.  **Install Playwright Browsers:**
    ```bash
    playwright install chromium
    ```
    *(You might need `python3 -m playwright install chromium`)*

4.  **Set up Environment Variables:**
    -   Create a `.env` file in the project root directory (where `requirements.txt` is).
    -   Add the following variables:
        ```dotenv
        # Supabase Credentials (obtain from your Supabase project settings)
        SUPABASE_URL=https://your_supabase_url.supabase.co
        SUPABASE_KEY=your_supabase_service_role_key # Service Role Key needed for uploads/bucket creation
        SUPABASE_BUCKET_NAME=your_image_bucket_name # e.g., xhs_image

        # Gemini API key (obtain from Google AI Studio)
        GEMINI_API_KEY="your_gemini_api_key"

        # Xiaohongshu Cookie (leave empty initially, will be filled by get_cookie.py)
        XHS_COOKIE=
        ```
    -   Replace placeholders with your actual credentials.

5.  **Prepare Dianping Environment:**
    -   Have an Android emulator (like MuMu, Nox, etc.) or a phone mirroring setup running.
    -   Ensure the Dianping app is installed and visible on the screen.

6.  **Initial Dianping Location Setup:**
    -   Run the location script **once** initially or whenever the emulator window position/size changes.
    -   Navigate manually to the Dianping app's main/home screen within the emulator/mirrored device **before** running the script.
    ```bash
    python3 dzdp_crawler/Locate.py
    ```
    -   Follow the on-screen prompts to move your mouse cursor to the specified elements and press Enter.
    -   **Crucially, do not move or resize the emulator/mirroring window after running `Locate.py`**.

## Usage

1.  **Configure the Pipeline:**
    -   Edit `main/config.py`:
        -   `SELECTED_RANKINGS`: List the exact Dianping ranking names you want to use to source brands.
        -   `CITIES`: List the cities you want the Dianping crawler to process.
        -   `RELOCATE_EMULATOR`: Set to `True` if you need to run the `Locate.py` setup, `False` otherwise.
        -   `GET_NEW_XHS_COOKIE`: Set to `True` the first time or if your cookie expires. Requires manual login via the browser opened by `get_cookie.py`. Set to `False` afterwards.
        -   `OPEN_NEW_BROWSER`: Set to `True` the first time to launch the persistent browser for XHS. Set to `False` if the browser from `openbrowser.py` is already running in the background.
        -   `PERFORM_CLEANUP`: Set to `True` to run the cleanup script at the end, `False` to keep temporary files.
    -   Edit `xhs_crawler/config.py`:
        -   `LIKE_THRESHOLD`: Set the minimum like count for XHS posts to be scraped.
        -   (The `BRANDS` list here is automatically overwritten by `main/get_brand.py`).

2.  **Run the Main Pipeline:**
    ```bash
    python3 main/main.py
    ```
    - The script will execute the different modules based on the configuration in `main/config.py`.
    - Follow any prompts (e.g., for initial XHS login if `GET_NEW_XHS_COOKIE` is `True`).

3.  **Stopping the Persistent Browser:** If you started the persistent browser (`openbrowser.py` either directly or via `main.py` with `OPEN_NEW_BROWSER=True`), you can stop it by pressing `Ctrl+C` in the terminal where `openbrowser.py` is running (if run directly) or it will be stopped automatically if the main script terminates it (depending on implementation details not fully visible).

4.  **Cleanup (Optional):**
    - If `PERFORM_CLEANUP` is `False` in `main/config.py`, you can run the cleanup script manually:
    ```bash
    python3 main/clean.py
    ```
    - Follow the prompt to confirm deletion of temporary data.

## Configuration Files

-   **`.env`:** Stores sensitive API keys and credentials. **Do not commit this file to version control.**
-   **`main/config.py`:** Main pipeline control. Defines cities for DZDP, rankings to source brands from, and flags to control automation steps (location setup, cookie acquisition, browser opening, cleanup).
-   **`dzdp_crawler/Config.py`:** Stores coordinates located by `Locate.py` and DZDP-specific settings like scroll times. Updated automatically by `Locate.py` and `main/main.py` (for cities).
-   **`xhs_crawler/config.py`:** Stores XHS like threshold and handles loading/saving the XHS cookie from/to `.env`. The `BRANDS` list is updated automatically by `main/get_brand.py`.

## Dependencies

Required Python packages are listed in `requirements.txt`:

```
pyautogui==0.9.54
pyperclip==1.8.2
Pillow==10.0.0
python-dotenv==1.0.1
google-generativeai==0.3.1
supabase==2.3.5
playwright==1.42.0
json5==0.9.24
tqdm==4.66.2
requests
```

Install them using `pip install -r requirements.txt`. 