#!/usr/bin/env python3
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

QUERY = """
SELECT
    r.id,
    COALESCE(ra.category, 'other') AS category,
    COALESCE(ra.severity, 1) AS severity,
    EXTRACT(DOW  FROM r.created_at) AS day_of_week,
    EXTRACT(HOUR FROM r.created_at) AS hour_of_day
FROM reports r
LEFT JOIN report_analysis ra ON ra.report_id = r.id
WHERE r.created_at > NOW() - INTERVAL '90 days'
  AND r.report_status IN ('complete', 'completed')
  AND ra.category IS NOT NULL
"""

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS temporal_patterns (
    id SERIAL PRIMARY KEY,
    day_of_week INT,
    hour_of_day INT,
    category TEXT,
    incident_count INT,
    avg_severity NUMERIC(5,2),
    risk_level TEXT,
    last_updated TIMESTAMP
)
"""


def risk_level(row):
    if row["avg_severity"] >= 4 and row["incident_count"] >= 3:
        return "critical"
    elif row["avg_severity"] >= 3 and row["incident_count"] >= 3:
        return "high"
    elif row["avg_severity"] >= 2 or row["incident_count"] >= 5:
        return "medium"
    return "low"


def main():
    db_url = os.getenv("DB_CONNECTION")
    if not db_url:
        print("Error: DB_CONNECTION not set")
        return

    engine = create_engine(db_url)
    df = pd.read_sql(QUERY, engine)

    if len(df) == 0:
        print("No reports found")
        return

    print(f"Loaded {len(df)} reports")

    patterns = (
        df.groupby(["day_of_week", "hour_of_day", "category"])
        .agg({"severity": "mean", "id": "count"})
        .reset_index()
    )
    patterns.columns = ["day_of_week", "hour_of_day", "category", "avg_severity", "incident_count"]
    patterns["risk_level"] = patterns.apply(risk_level, axis=1)
    patterns["last_updated"] = datetime.now()

    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE))
        conn.execute(text("TRUNCATE TABLE temporal_patterns"))

    patterns.to_sql("temporal_patterns", engine, if_exists="append", index=False)
    print(f"Saved {len(patterns)} temporal patterns")


if __name__ == "__main__":
    main()
