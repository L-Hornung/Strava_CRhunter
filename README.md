# Strava Segment Analysis 

This project provides tools for analyzing running segments from Strava using the Strava API. It focuses on identifying segments around a location that have slower course records (CRs), which may still be achievable, while filtering out segments with unrealistic times that are faster than the world record.

## Features

- Fetch and analyze Strava segments around a given location  
- Identify segments with slow CRs that are realistically achievable  
- Filter out segments with impossible times (faster than the world record)  
- Calculate pace and compare to world record paces  
- Handle Strava API rate limits automatically  
- Securely manage your Strava API token using a `.env` file  

## Usage

1. Clone the repository.  
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your Strava API token:
   ```env
   STRAVA_ACCESS_TOKEN=your_token_here
   ```
4. Add your location in main.py
5. Run the main script:
   ```bash
   python main.py
   ```

## Project Structure

- `main.py` – Main entry point for segment analysis  
- `strava/` – Strava API client  
- `analysis/` – Segment analysis, including filtering unrealistic CRs and identifying achievable segments  
- `models/` – Data models  
- `utils/` – Utility functions for segment exploration  

## Security

- **Never commit your `.env` file or API token to GitHub!**  
- Add `.env` to your `.gitignore` file.  

## Notes

- The Strava API has strict rate limits. The code automatically waits if the limit is reached.  
- For large areas, the code splits the search into smaller grid cells to collect more segments.  

## Use Case

This project addresses a common issue on Strava: many segments have course records (CRs) that are unrealistic or humanly impossible. These times can result from GPS errors or incorrect activity types (e.g., cycling instead of running).  

The tool:

1. Filters out segments with times faster than the world record.  
2. Sorts the remaining segments by **slowest CRs first**, helping athletes identify segments that are realistically possible to target and improve.  
3. Compares segment paces to world record paces for additional insight.  

By focusing on achievable segments, athletes can efficiently plan new personal records (PRs) and target realistic goals.  

