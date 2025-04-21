# Restaurant AI Data Pipeline

A comprehensive data pipeline for restaurant market intelligence that combines data from Dianping (DZDP) and Xiaohongshu (XHS).

## System Requirements

- **Python 3.11** (specifically downgraded from 3.12 for compatibility)
- macOS (tested on macOS Sonoma/Ventura)
- Supabase account with proper tables setup
- Android emulator or iPhone mirroring for Dianping access

## Project Structure

```
restaurant_ai/
├── dzdp_crawler/        # Dianping crawler module
│   ├── 分析结果文件/     # Analysis result files (JSON)
│   ├── 搜索结果截图/     # Search result screenshots
│   ├── Locate.py        # Locate UI elements in emulator
│   ├── Search.py        # Search and collect data
│   ├── Analyzer.py      # Analyze collected data
│   └── Upload.py        # Upload results to Supabase
│
├── xhs_crawler/         # Xiaohongshu crawler module
│   ├── data/            # Data storage
│   ├── browser_data/    # Browser profile data
│   ├── crawler.py       # Main crawler script
│   ├── upload.py        # Upload data to Supabase
│   └── image_direct_upload.py  # Upload images to Supabase
│
├── main/                # Main pipeline controller
│   ├── config.py        # Central configuration
│   ├── main.py          # Main pipeline orchestrator
│   ├── refresh.py       # Refresh brand data
│   ├── get_brand.py     # Extract brand data for XHS
│   └── clean.py         # Cleanup temporary files
│
├── .env                 # Environment variables (Supabase credentials)
└── requirements.txt     # Python dependencies
```

## Setup Instructions

1. **Python Environment Setup**

   ```bash
   # Create a virtual environment with Python 3.11
   python3.11 -m venv .venv311
   source .venv311/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Environment Configuration**

   Copy `.env.example` to `.env` and fill in your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Configure Targets**

   Edit `main/config.py` to set:
   - `CITIES`: List of cities to crawl from Dianping
   - `SELECTED_RANKINGS`: List of rankings to extract brands from
   - Automation settings like `RELOCATE_EMULATOR`, `GET_NEW_XHS_COOKIE`, etc.

## Workflow

The workflow is divided into distinct modules:

### Module 1: Preparation
- Initialize browser session for XHS if needed
- Set up emulator/device location for DZDP

### Module 2: Dianping (DZDP) Crawling
1. Update city list in DZDP config
2. Search for restaurants in target cities
3. Analyze search results
4. Upload data to Supabase

### Module 3: Xiaohongshu (XHS) Crawling
1. Refresh brand data from DZDP data in Supabase
2. Update XHS configuration with brand names
3. Crawl XHS for posts related to these brands
4. Upload data and images to Supabase

### Module 4: Cleanup
- Clean temporary files if configured

## Running the Pipeline

### Full Pipeline
```bash
python3 main/main.py
```

### Individual Components
You can run specific parts of the pipeline:

```bash
# DZDP Crawler components
python3 dzdp_crawler/Locate.py
python3 dzdp_crawler/Search.py
python3 dzdp_crawler/Analyzer.py
python3 dzdp_crawler/Upload.py

# XHS Crawler components
python3 xhs_crawler/get_cookie.py
python3 xhs_crawler/openbrowser.py
python3 xhs_crawler/crawler.py
python3 xhs_crawler/upload.py
python3 xhs_crawler/image_direct_upload.py

# Data processing components
python3 main/refresh.py
python3 main/get_brand.py
```

## Working with Specific City Data

To focus on a single city's data (e.g., Wuhan):

1. Keep only that city's folder in `dzdp_crawler/分析结果文件/`
2. Edit `main/config.py` to include only that city in the `CITIES` list
3. Run the upload process: `python3 dzdp_crawler/Upload.py`
4. Process the data: `python3 main/refresh.py` and `python3 main/get_brand.py`
5. Run the XHS crawler components

## Known Issues and Fixes

### F-string Expression Limitation
Python 3.11 has a limitation where f-string expressions cannot contain backslashes. 
This has been fixed in the codebase by separating string operations with backslashes 
from the f-string expressions.

### Supabase Client Issues
If encountering proxy errors with the Supabase client, update the packages:
```bash
pip install -U supabase gotrue
```

## Data Flow

1. Dianping data is collected and saved as JSON files
2. These files are uploaded to Supabase's "dzdpdata" table
3. Brand information is extracted from this table
4. XHS crawler searches for these brands on Xiaohongshu
5. XHS data is uploaded to Supabase

## Maintenance

- To clean all temporary data: `python3 main/clean.py`
- Make sure your `.env` file has valid credentials
- Check `timer_log.txt` for execution time logs

## License

Proprietary - All Rights Reserved 