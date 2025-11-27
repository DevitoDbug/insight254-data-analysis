#!/usr/bin/env python3
"""
Temporal Pattern Analysis
Identifies high-risk time periods (day of week + hour of day)
"""

import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


def main():
    print(f"⏰ Starting temporal pattern analysis - {datetime.now()}")

    # Database connection
    db_url = os.getenv("DB_CONNECTION")
    if not db_url:
        print("❌ DB_CONNECTION not set in .env file")
        return

    engine = create_engine(db_url)

    # Fetch reports from last 90 days
    query = """
    SELECT 
        r.id,
        COALESCE(ra.category, 'other') as category,
        COALESCE(ra.severity, 1) as severity,
        r.created_at,
        EXTRACT(DOW FROM r.created_at) as day_of_week,
        EXTRACT(HOUR FROM r.created_at) as hour_of_day
    FROM reports r
    LEFT JOIN report_analysis ra ON ra.report_id = r.id
    WHERE r.created_at > NOW() - INTERVAL '90 days'
      AND r.report_status IN ('complete', 'completed')
      AND ra.category IS NOT NULL
    """

    print("📊 Fetching reports from database...")
    df = pd.read_sql(query, engine)

    if len(df) == 0:
        print("⚠️  No reports found")
        return

    print(f"✅ Found {len(df)} reports")

    # Group by time patterns
    patterns = (
        df.groupby(["day_of_week", "hour_of_day", "category"])
        .agg({"severity": "mean", "id": "count"})
        .reset_index()
    )

    patterns.columns = [
        "day_of_week",
        "hour_of_day",
        "category",
        "avg_severity",
        "incident_count",
    ]

    # Determine risk level
    def get_risk_level(row):
        if row["avg_severity"] >= 4 and row["incident_count"] >= 3:
            return "high"
        elif row["avg_severity"] >= 3 or row["incident_count"] >= 5:
            return "medium"
        else:
            return "low"

    patterns["risk_level"] = patterns.apply(get_risk_level, axis=1)
    patterns["last_updated"] = datetime.now()

    # Save to database
    print(f"💾 Saving {len(patterns)} temporal patterns to database...")

    with engine.begin() as conn:
        # Create table if not exists
        conn.execute(
            text(
                """
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
            )
        )

        # Clear old data
        conn.execute(text("TRUNCATE TABLE temporal_patterns"))

    # Insert new data
    patterns.to_sql("temporal_patterns", engine, if_exists="append", index=False)

    print(f"✅ Temporal analysis complete!")

    # Display high-risk periods
    high_risk = patterns[patterns["risk_level"] == "high"].sort_values(
        "incident_count", ascending=False
    )

    days = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    print(f"\n🚨 High-Risk Time Periods ({len(high_risk)} found):")
    for idx, row in high_risk.head(10).iterrows():
        day_name = days[int(row["day_of_week"])]
        hour = int(row["hour_of_day"])
        print(
            f"   {day_name} {hour:02d}:00-{hour+1:02d}:00 | "
            f"{row['category']:15s} | "
            f"{row['incident_count']:3.0f} incidents | "
            f"Severity: {row['avg_severity']:.2f}"
        )


if __name__ == "__main__":
    main()
