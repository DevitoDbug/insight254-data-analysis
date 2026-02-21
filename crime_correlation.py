#!/usr/bin/env python3
import os
from datetime import datetime

import numpy as np
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
    COALESCE(ra.category, 'other') AS category,
    COALESCE(ra.severity, 1) AS severity,
    r.created_at,
    EXTRACT(DOW  FROM r.created_at) AS day_of_week,
    EXTRACT(HOUR FROM r.created_at) AS hour_of_day
FROM reports r
LEFT JOIN report_analysis ra ON ra.report_id = r.id
WHERE r.created_at > NOW() - INTERVAL '60 days'
  AND r.latitude IS NOT NULL
  AND r.longitude IS NOT NULL
  AND ra.category IS NOT NULL
  AND r.report_status IN ('complete', 'completed')
"""

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS crime_correlations (
    id SERIAL PRIMARY KEY,
    cluster_id TEXT,
    category TEXT,
    incident_count INT,
    center_lat NUMERIC(10,8),
    center_lng NUMERIC(11,8),
    avg_severity NUMERIC(5,2),
    time_span_days INT,
    most_common_day INT,
    most_common_hour INT,
    is_likely_organized BOOLEAN,
    confidence_score NUMERIC(3,2),
    last_updated TIMESTAMP
)
"""


def _mode_or_none(series):
    m = series.mode()
    return int(m.iloc[0]) if not m.empty else None


def main():
    db_url = os.getenv("DB_CONNECTION")
    if not db_url:
        print("Error: DB_CONNECTION not set")
        return

    engine = create_engine(db_url)
    df = pd.read_sql(QUERY, engine)

    if len(df) < 10:
        print("Not enough data for correlation analysis (need >= 10 reports)")
        return

    print(f"Loaded {len(df)} reports")

    correlations = []

    for category, cat_df in df.groupby("category"):
        if pd.isna(category) or len(cat_df) < 5:
            continue

        cat_df = cat_df.copy()

        # Multi-dimensional clustering: location (70 %) + time (30 %)
        coords = cat_df[["latitude", "longitude"]].values
        time_feat = cat_df[["day_of_week", "hour_of_day"]].values / [7.0, 24.0]
        features = np.hstack([coords * 0.7, time_feat * 0.3])

        labels = DBSCAN(eps=0.05, min_samples=3).fit_predict(features)
        cat_df["cluster"] = labels

        for cid, grp in cat_df[cat_df["cluster"] != -1].groupby("cluster"):
            if len(grp) < 3:
                continue

            span_days = (grp["created_at"].max() - grp["created_at"].min()).days
            avg_sev = grp["severity"].mean()
            count = len(grp)

            is_organized = count >= 4 and span_days <= 45 and avg_sev >= 2.5
            confidence = min(
                (count / 10) * 0.4
                + (1 - span_days / 60) * 0.3
                + (avg_sev / 5) * 0.3,
                1.0,
            )

            correlations.append({
                "cluster_id": f"{category}_{cid}",
                "category": category,
                "incident_count": count,
                "center_lat": grp["latitude"].mean(),
                "center_lng": grp["longitude"].mean(),
                "avg_severity": avg_sev,
                "time_span_days": span_days,
                "most_common_day": _mode_or_none(grp["day_of_week"]),
                "most_common_hour": _mode_or_none(grp["hour_of_day"]),
                "is_likely_organized": is_organized,
                "confidence_score": confidence,
                "last_updated": datetime.now(),
            })

    if not correlations:
        print("No significant correlations detected")
        return

    result = pd.DataFrame(correlations)

    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE))
        conn.execute(text("TRUNCATE TABLE crime_correlations"))

    result.to_sql("crime_correlations", engine, if_exists="append", index=False)
    print(f"Saved {len(result)} correlations")


if __name__ == "__main__":
    main()
