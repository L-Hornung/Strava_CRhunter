import math
import time
from analysis.segment_analysis import analyze_effort

def bounding_box(lat, lng, radius_km):
    """Calculates bounding box for Strava API: [lat_min, lng_min, lat_max, lng_max]"""
    lat_delta = radius_km / 110.574
    lng_delta = radius_km / (111.320 * math.cos(math.radians(lat)))
    return [lat - lat_delta, lng - lng_delta, lat + lat_delta, lng + lng_delta]


def explore_segments(client, bounds, activity_type="running"):
    """
    Retrieves segments from a bounding box area and filters by activity_type.
    activity_type: "Run" or "Ride"
    """
    url = "https://www.strava.com/api/v3/segments/explore"
    params = {
        "bounds": ",".join(map(str, bounds)),
        "activity_type": activity_type,  # Filter here
        "min_cat": 0,
        "max_cat": 5
    }

    resp = client._get(url, params=params)
    segments = resp.get("segments", [])

    return segments

def explore_run_segments_with_details(client, center_lat, center_lng, min_segments=50, initial_radius_km=0.1, max_radius_km=10.0, debug=False):
    """
    Returns at least `min_segments` running segments as resource_state=3 objects.
    The search area is split into a grid to bypass the 10-segment limit per API call.
    """
    all_segments = []
    current_radius = initial_radius_km
    grid_size = 2  # Start with 2x2 grid, can be increased for larger areas

    while len(all_segments) < min_segments and current_radius <= max_radius_km:
        if debug:
            print(f"[DEBUG] Querying Explorer API | Radius: {current_radius} km")

        bounds = bounding_box(center_lat, center_lng, current_radius)
        lat_min, lng_min, lat_max, lng_max = bounds
        lat_step = (lat_max - lat_min) / grid_size
        lng_step = (lng_max - lng_min) / grid_size

        # Query each grid cell
        for i in range(grid_size):
            for j in range(grid_size):
                cell_bounds = [
                    lat_min + i * lat_step,
                    lng_min + j * lng_step,
                    lat_min + (i + 1) * lat_step,
                    lng_min + (j + 1) * lng_step
                ]
                summary_segments = explore_segments(client, cell_bounds)
                time.sleep(1)  # Add a 1 second pause after each API call to reduce request frequency
                if debug:
                    print(f"[DEBUG] Grid cell {i},{j} found {len(summary_segments)} summary segments")
                segment_ids = [s["id"] for s in summary_segments]
                for seg_id in segment_ids:
                    try:
                        detail = client.get_segment(seg_id)
                        time.sleep(1)  # Add a 1 second pause after each detail API call
                        if detail.get("activity_type") == "Run":
                            if detail["id"] not in [seg["id"] for seg in all_segments]:
                                all_segments.append(detail)
                                if debug:
                                    print(f"[DEBUG] Running segment added: {detail['name']} ({detail['distance']} m)")
                        else:
                            if debug:
                                print(f"[DEBUG] Segment ignored, not running: {detail.get('activity_type', '?')} {detail.get('name', '?')}")
                        if len(all_segments) >= min_segments:
                            break
                    except Exception as e:
                        if debug:
                            print(f"[DEBUG] Error retrieving detail segment {seg_id}: {e}")
                        continue
                if len(all_segments) >= min_segments:
                    break
            if len(all_segments) >= min_segments:
                break
        if len(all_segments) < min_segments:
            current_radius *= 2
            grid_size += 1  # Increase grid density for larger areas
            if debug:
                print(f"[DEBUG] Less than {min_segments} segments, radius increased to {current_radius} km, grid size {grid_size}x{grid_size}")
    return all_segments[:min_segments]



def analyze_segments_around(client, center_lat, center_lng, radius_km, user_max_pace_s_per_km=220, debug=False, max_segments=50):
    """
    Always returns a list of segments for analysis:
    - primarily own segments / efforts
    - optionally popular segments via Explorer API
    """
    results = []

    # 1 Explorer API (popular segments)
    bounds = bounding_box(center_lat, center_lng, radius_km)
    if debug:
        print(f"[DEBUG] Bounding Box: {bounds} | Radius: {radius_km} km")

    try:
        segments = explore_run_segments_with_details(client, center_lat, center_lng, min_segments=max_segments, initial_radius_km=radius_km, max_radius_km=10.0, debug=debug)
        if debug:
            print(f"[DEBUG] Explorer API segments found: {len(segments)}")
    except Exception as e:
        segments = []
        if debug:
            print(f"[DEBUG] Explorer API error: {e}")
        # Print full stack trace for easier debugging
        import traceback
        traceback.print_exc()

    for segment in segments:
        # Check if XOM is present
        xoms = segment.get("xoms")
        if not xoms or "overall" not in xoms:
            if debug:
                print(f"[DEBUG] Segment without XOM: {segment.get('name', '?')} ({segment.get('distance', '?')} m)")
            continue  # Skip, as no KOM/XOM data available

        try:
            kom_time_s = parse_kom_time(segment["xoms"]["overall"])
        except Exception as e:
            if debug:
                print(f"[DEBUG] Error parsing KOM for segment {segment.get('name', '?')}: {e}")
            continue

        distance_m = segment["distance"]
        analysis = analyze_effort(distance_m, kom_time_s)

        if analysis["flag"] == "impossible":
            category = "impossible"
        elif analysis["pace_s_per_km"] < user_max_pace_s_per_km:
            category = "potentially achievable"
        else:
            category = "valid but not solvable"

        results.append({
            "name": segment["name"],
            "distance_m": distance_m,
            "kom_s": kom_time_s,
            "pace_s_per_km": analysis["pace_s_per_km"],
            "wr_pace_s_per_km": analysis["wr_pace_s_per_km"],
            "flag": analysis["flag"],
            "category": category,
            "id": segment["id"]
        })
    #sort by slowest pace first
    results_sorted = sorted(results, key=lambda x: x["pace_s_per_km"], reverse=True)
    return results_sorted


def parse_kom_time(kom_raw):
    """
    Converts KOM time to seconds
    kom_raw: e.g. "13s" or "6:36" or values with comma or invalid formats
    Handles cases like '200,2000' robustly.
    """
    try:
        # Remove all non-digit, non-colon, non-s characters
        import re
        kom_raw_clean = re.sub(r'[^0-9:s]', '', kom_raw)
        # If there is a colon, treat as mm:ss
        if ':' in kom_raw_clean:
            parts = kom_raw_clean.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            else:
                print(f"[DEBUG] Unexpected time format: {kom_raw}")
                return None
        # If ends with 's', treat as seconds
        elif kom_raw_clean.endswith('s'):
            kom_raw_clean = kom_raw_clean.replace('s', '')
            return int(kom_raw_clean)
        # If only digits, treat as seconds
        elif kom_raw_clean.isdigit():
            return int(kom_raw_clean)
        else:
            # Try to extract first number
            numbers = re.findall(r'\d+', kom_raw_clean)
            if numbers:
                return int(numbers[0])
            print(f"[DEBUG] Could not parse KOM time: {kom_raw}")
            return None
    except Exception as e:
        print(f"[DEBUG] Error parsing KOM time '{kom_raw}': {e}")
        return None
