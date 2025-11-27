#!/usr/bin/env python3
"""
Crime Correlation Analysis
Detects patterns suggesting organized crime or related incidents
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import DBSCAN
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


def main():
    print(f"🔗 Starting crime correlation analysis - {datetime.now()}")

    # Database connection
    db_url = os.getenv("DB_CONNECTION")
    if not db_url:
        print("❌ DB_CONNECTION not set in .env file")
        return

    engine = create_engine(db_url)

    # Fetch reports with analysis data
    query = """
    SELECT 
        r.id,
        r.latitude::float as latitude,
        r.longitude::float as longitude,
        COALESCE(ra.category, 'other') as category,
        COALESCE(ra.severity, 1) as severity,
        r.created_at,
        EXTRACT(DOW FROM r.created_at) as day_of_week,
        EXTRACT(HOUR FROM r.created_at) as hour_of_day,
        ra.entities::text as entities
    FROM reports r
    LEFT JOIN report_analysis ra ON ra.report_id = r.id
    WHERE r.created_at > NOW() - INTERVAL '60 days'
      AND r.latitude IS NOT NULL
      AND r.longitude IS NOT NULL
      AND ra.category IS NOT NULL
      AND r.report_status IN ('complete', 'completed')
    """

    print("📊 Fetching reports from database...")
    df = pd.read_sql(query, engine)

    if len(df) < 10:
        print("⚠️  Not enough data for correlation analysis (need at least 10 reports)")
        return

    print(f"✅ Found {len(df)} reports")

    correlations = []

    # Group by category for targeted analysis
    for category in df["category"].unique():
        if pd.isna(category):
            continue

        category_df = df[df["category"] == category].copy()

        if len(category_df) < 5:
            continue

        # Multi-dimensional clustering: location + time
        # Normalize coordinates and time
        coords = category_df[["latitude", "longitude"]].values
        time_features = category_df[["day_of_week", "hour_of_day"]].values / [7.0, 24.0]

        # Combine location (weighted 70%) and time (weighted 30%)
        features = np.hstack([coords * 0.7, time_features * 0.3])

        # DBSCAN clustering
        clustering = DBSCAN(eps=0.05, min_samples=3).fit(features)
        category_df["correlation_cluster"] = clustering.labels_

        # Analyze each cluster
        for cluster_id in category_df["correlation_cluster"].unique():
            if cluster_id == -1:  # Skip noise
                continue

            cluster_df = category_df[category_df["correlation_cluster"] == cluster_id]

            if len(cluster_df) < 3:
                continue

            # Calculate cluster statistics
            correlation = {
                "cluster_id": f"{category}_{cluster_id}",
                "category": category,
                "incident_count": len(cluster_df),
                "center_lat": cluster_df["latitude"].mean(),
                "center_lng": cluster_df["longitude"].mean(),
                "avg_severity": cluster_df["severity"].mean(),
                "time_span_days": (
                    cluster_df["created_at"].max() - cluster_df["created_at"].min()
                ).days,
                "most_common_day": (
                    int(cluster_df["day_of_week"].mode()[0])
                    if len(cluster_df["day_of_week"].mode()) > 0
                    else None
                ),
                "most_common_hour": (
                    int(cluster_df["hour_of_day"].mode()[0])
                    if len(cluster_df["hour_of_day"].mode()) > 0
                    else None
                ),
                "last_updated": datetime.now(),
            }

            # Determine if it's likely organized crime
            # Indicators: multiple incidents, same time pattern, similar location
            is_organized = (
                correlation["incident_count"] >= 4
                and correlation["time_span_days"] <= 45
                and correlation["avg_severity"] >= 2.5
            )

            correlation["is_likely_organized"] = is_organized
            correlation["confidence_score"] = min(
                (correlation["incident_count"] / 10) * 0.4
                + (1 - correlation["time_span_days"] / 60) * 0.3
                + (correlation["avg_severity"] / 5) * 0.3,
                1.0,
            )

            correlations.append(correlation)

    if len(correlations) == 0:
        print("⚠️  No significant correlations detected")
        return

    correlations_df = pd.DataFrame(correlations)

    # Save to database
    print(f"💾 Saving {len(correlations_df)} correlations to database...")

    with engine.begin() as conn:
        # Create table if not exists
        conn.execute(
            text(
                """
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
            )
        )

        # Clear old data
        conn.execute(text("TRUNCATE TABLE crime_correlations"))

    # Insert new data
    correlations_df.to_sql(
        "crime_correlations", engine, if_exists="append", index=False
    )

    print(f"✅ Crime correlation analysis complete!")

    # Display likely organized crime patterns
    organized = correlations_df[
        correlations_df["is_likely_organized"] == True
    ].sort_values("confidence_score", ascending=False)

    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    print(f"\n🎯 Likely Organized Crime Patterns ({len(organized)} found):")
    for idx, row in organized.head(10).iterrows():
        day_name = (
            days[int(row["most_common_day"])]
            if pd.notna(row["most_common_day"])
            else "N/A"
        )
        hour = (
            int(row["most_common_hour"]) if pd.notna(row["most_common_hour"]) else "N/A"
        )
        print(
            f"   Cluster: {row['cluster_id']:20s} | "
            f"{row['incident_count']:2.0f} incidents | "
            f"{day_name} {hour:02d}:00 | "
            f"Confidence: {row['confidence_score']:.2f}"
        )


if __name__ == "__main__":
    main()
