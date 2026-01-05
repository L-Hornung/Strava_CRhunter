import os
from dotenv import load_dotenv
from client import StravaClient
from analysis.segment_analysis import analyze_effort, export_results_to_excel
from utils.segment_explore import bounding_box, explore_segments, analyze_segments_around

# -------------------------
# Environment & Strava Client
# -------------------------
load_dotenv()
client = StravaClient(os.getenv("STRAVA_ACCESS_TOKEN"))
# Example location: Berlin
center_lat, center_lng = 52.513673468165, 13.474815751923392
radius_km = 1

debug = True  # Set this to False to disable debug output everywhere
max_segments = 70  # Set the maximum number of segments to analyze

results_around = analyze_segments_around(client, center_lat, center_lng, radius_km, debug=debug, max_segments=max_segments)
if len(results_around) < 1:
    print("Strava not responding")
else:
    print(f"{len(results_around)} segments in the extended area:")
    for r in results_around:
        print(f"{r['name']} | KOM: {r['kom_s']} s | "
              f"Pace: {r['pace_s_per_km']} s/km | WR Pace: {r['wr_pace_s_per_km']} s/km | Flag: {r['flag']} | ID: {r['id']}")

    print("\nSegments in the extended area containing an error:")
    for r in results_around:
        if r['flag'] == "impossible":
            print(f"{r['name']} | KOM: {r['kom_s']} s | "
                  f"Pace: {r['pace_s_per_km']} s/km | WR Pace: {r['wr_pace_s_per_km']} s/km | Flag: {r['flag']}| ID: {r['id']}")

    export_results_to_excel(results_around, filename="segment_analysis.xlsx")