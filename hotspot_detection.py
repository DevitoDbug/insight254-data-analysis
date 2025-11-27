#!/usr/bin/env python3
"""
Hotspot Detection - DBSCAN Clustering
Identifies geographical areas with high crime concentration
"""

import os
from datetime import datetime

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv
from sklearn.cluster import DBSCAN
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()


def main():
    print(f"🔍 Starting hotspot detection - {datetime.now()}")

    # Database connection
    db_url = os.getenv("DB_CONNECTION")
    if not db_url:
        print("❌ DB_CONNECTION not set in .env file")
        return

    engine = create_engine(db_url)

    # Fetch recent reports with location data
    query = """
    SELECT 
        r.id,
        r.latitude::float as latitude,
        r.longitude::float as longitude,
        COALESCE(ra.severity, 1) as severity,
        COALESCE(ra.category, 'other') as category,
        r.created_at,
        r.report_status
    FROM reports r
    LEFT JOIN report_analysis ra ON ra.report_id = r.id
    WHERE r.latitude IS NOT NULL 
      AND r.longitude IS NOT NULL
      AND r.created_at > NOW() - INTERVAL '30 days'
      AND r.report_status IN ('complete', 'completed')
    """

    print("📊 Fetching reports from database...")
    df = pd.read_sql(query, engine)

    if len(df) == 0:
        print("⚠️  No reports with location data found")
        return

    print(f"✅ Found {len(df)} reports with location data")

    # Perform DBSCAN clustering
    # eps=0.01 ≈ ~1km radius (for lat/lng coordinates)
    # min_samples=5 = minimum 5 incidents to form a hotspot
    coords = df[["latitude", "longitude"]].values
    clustering = DBSCAN(eps=0.01, min_samples=5).fit(coords)

    df["hotspot_id"] = clustering.labels_

    # Filter out noise (-1 means not part of any cluster)
    hotspots_df = df[df["hotspot_id"] != -1]

    if len(hotspots_df) == 0:
        print("⚠️  No hotspots detected (need at least 5 incidents within 1km)")
        return

    # Calculate hotspot statistics
    hotspot_stats = (
        hotspots_df.groupby("hotspot_id")
        .agg(
            {
                "latitude": "mean",
                "longitude": "mean",
                "severity": ["mean", "max"],
                "id": "count",
            }
        )
        .reset_index()
    )

    hotspot_stats.columns = [
        "hotspot_id",
        "center_lat",
        "center_lng",
        "avg_severity",
        "max_severity",
        "incident_count",
    ]

    # Find most common category per hotspot
    category_mode = (
        hotspots_df.groupby("hotspot_id")["category"]
        .agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else "other")
        .reset_index()
    )
    category_mode.columns = ["hotspot_id", "primary_category"]

    hotspot_stats = hotspot_stats.merge(category_mode, on="hotspot_id")

    # Add metadata
    hotspot_stats["radius_km"] = 1.0  # DBSCAN eps parameter
    hotspot_stats["last_updated"] = datetime.now()

    # Clear old data and insert new
    print(f"💾 Saving {len(hotspot_stats)} hotspots to database...")

    with engine.begin() as conn:
        # Create table if not exists
        conn.execute(
            text(
                """
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
            )
        )

        # Clear old data
        conn.execute(text("TRUNCATE TABLE hotspot_analysis"))

    # Insert new data
    hotspot_stats.to_sql("hotspot_analysis", engine, if_exists="append", index=False)

    print(f"✅ Hotspot detection complete!")
    print(f"\n📈 Summary:")
    print(f"   Total reports analyzed: {len(df)}")
    print(f"   Hotspots detected: {len(hotspot_stats)}")
    print(
        f"   Average incidents per hotspot: {hotspot_stats['incident_count'].mean():.1f}"
    )
    print(f"   Highest severity hotspot: {hotspot_stats['avg_severity'].max():.2f}")

    # Display top 5 hotspots
    print(f"\n🔥 Top 5 Hotspots:")
    top5 = hotspot_stats.nlargest(5, "incident_count")
    for idx, row in top5.iterrows():
        print(
            f"   Hotspot #{row['hotspot_id']}: {row['incident_count']} incidents, "
            f"Category: {row['primary_category']}, "
            f"Avg Severity: {row['avg_severity']:.2f}"
        )


if __name__ == "__main__":
    main()
