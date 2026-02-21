#!/usr/bin/env python3
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import DBSCAN
from sqlalchemy import create_engine, text

load_dotenv()

QUERY = """
SELECT
    r.id,
    r.latitude::float  AS latitude,
    r.longitude::float AS longitude,
    COALESCE(ra.severity, 1) AS severity,
    COALESCE(ra.category, 'other') AS category
FROM reports r
LEFT JOIN report_analysis ra ON ra.report_id = r.id
WHERE r.latitude IS NOT NULL
  AND r.longitude IS NOT NULL
  AND r.created_at > NOW() - INTERVAL '30 days'
  AND r.report_status IN ('complete', 'completed')
"""

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS hotspot_analysis (
    id SERIAL PRIMARY KEY,
    hotspot_id INT,
    center_lat NUMERIC(10,8),
    center_lng NUMERIC(11,8),
    incident_count INT,
    avg_severity NUMERIC(5,2),
    max_severity INT,
    primary_category TEXT,
    radius_km NUMERIC(5,2),
    last_updated TIMESTAMP
)
"""


def main():
    db_url = os.getenv("DB_CONNECTION")
    if not db_url:
        print("Error: DB_CONNECTION not set")
        return

    engine = create_engine(db_url)
    df = pd.read_sql(QUERY, engine)

    if len(df) == 0:
        print("No reports with location data found")
        return

    print(f"Loaded {len(df)} reports")

    # eps ≈ 1 km radius, min 5 incidents to form a cluster
    clustering = DBSCAN(eps=0.01, min_samples=5).fit(
        df[["latitude", "longitude"]].values
    )
    df["hotspot_id"] = clustering.labels_

    hotspots_df = df[df["hotspot_id"] != -1]
    if len(hotspots_df) == 0:
        print("No hotspots detected (need >= 5 incidents within ~1 km)")
        return

    stats = (
        hotspots_df.groupby("hotspot_id")
        .agg({"latitude": "mean", "longitude": "mean", "severity": ["mean", "max"], "id": "count"})
        .reset_index()
    )
    stats.columns = ["hotspot_id", "center_lat", "center_lng", "avg_severity", "max_severity", "incident_count"]

    category_mode = (
        hotspots_df.groupby("hotspot_id")["category"]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "other")
        .reset_index()
    )
    category_mode.columns = ["hotspot_id", "primary_category"]
    stats = stats.merge(category_mode, on="hotspot_id")
    stats["radius_km"] = 1.0
    stats["last_updated"] = datetime.now()

    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE))
        conn.execute(text("TRUNCATE TABLE hotspot_analysis"))

    stats.to_sql("hotspot_analysis", engine, if_exists="append", index=False)
    print(f"Saved {len(stats)} hotspots")


if __name__ == "__main__":
    main()
