from analysis.world_records import interpolate_world_record
from .world_records import WORLD_RECORDS, interpolate_world_record
import pandas as pd

from typing import Optional

def analyze_effort(distance_m: Optional[float], elapsed_time_s: Optional[float]) -> dict:
    """
    Analyzes a running segment effort:
    - distance_m: distance in meters
    - elapsed_time_s: time in seconds (KOM)

    Returns:
    {
        "elapsed_time_s": int | None,
        "pace_s_per_km": float | None,
        "wr_pace_s_per_km": float | None,
        "ratio": float | None,
        "flag": str
    }
    """

    # ---------- Guard clauses ----------
    if distance_m is None or elapsed_time_s is None:
        return {
            "elapsed_time_s": elapsed_time_s,
            "pace_s_per_km": None,
            "wr_pace_s_per_km": None,
            "ratio": None,
            "flag": "no_data"
        }

    if distance_m <= 0:
        return {
            "elapsed_time_s": elapsed_time_s,
            "pace_s_per_km": None,
            "wr_pace_s_per_km": None,
            "ratio": None,
            "flag": "invalid_distance"
        }

    # ---------- Athlete pace ----------
    pace_s_per_km = elapsed_time_s / (distance_m / 1000)

    # ---------- World record interpolation ----------
    wr_time_s = interpolate_world_record(distance_m)

    if wr_time_s is None:
        # Extremely short or unsupported distance
        flag = "impossible"
        wr_time_s = elapsed_time_s  # safe fallback to avoid None
    else:
        ratio = elapsed_time_s / wr_time_s
        flag = "impossible" if ratio < 0.8 else "plausible"

    # ---------- WR pace ----------
    wr_pace_s_per_km = wr_time_s / (distance_m / 1000)

    # ---------- Result ----------
    return {
        "elapsed_time_s": int(elapsed_time_s),
        "pace_s_per_km": round(pace_s_per_km, 1),
        "wr_pace_s_per_km": round(wr_pace_s_per_km, 1),
        "ratio": round(elapsed_time_s / wr_time_s, 2),
        "flag": flag
    }


def export_results_to_excel(results_around, filename="segment_analysis.xlsx"):
    if not results_around:
        print("Keine Ergebnisse zum Exportieren.")
        return

    # Gesamte Ergebnisliste
    df_all = pd.DataFrame(results_around)

    # Nur fehlerhafte / unmögliche Segmente
    df_impossible = df_all[df_all["flag"] == "impossible"]

    # Spalten-Reihenfolge (optional, aber sauber)
    columns_order = [
        "name",
        "id",
        "kom_s",
        "pace_s_per_km",
        "wr_pace_s_per_km",
        "flag"
    ]

    df_all = df_all.reindex(columns=columns_order)
    df_impossible = df_impossible.reindex(columns=columns_order)

    # Excel schreiben
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df_all.to_excel(writer, sheet_name="All Segments", index=False)
        df_impossible.to_excel(writer, sheet_name="Impossible Segments", index=False)

    print(f"Excel-Datei erstellt: {filename}")
