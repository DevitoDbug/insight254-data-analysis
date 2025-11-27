# ✅ Python Analytics Setup Complete!

## What's Installed

### Files Created:
- ✅ `hotspot_detection.py` - DBSCAN clustering for crime hotspots
- ✅ `temporal_analysis.py` - Time pattern detection (day/hour)
- ✅ `crime_correlation.py` - Organized crime detection
- ✅ `run_analytics.sh` - Run all scripts at once
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env` - Database connection (copied from backend)
- ✅ `venv/` - Python virtual environment with all packages

### Python Packages Installed (in venv):
- pandas 2.1.4
- numpy 1.26.2
- scikit-learn 1.3.2
- geopandas 0.14.1
- shapely 2.0.2
- psycopg2-binary 2.9.9
- sqlalchemy 2.0.23
- python-dotenv 1.0.0

---

## Quick Start

### Test the Setup:
```bash
cd data-analysis
source venv/bin/activate
python hotspot_detection.py
```

### Run All Analytics:
```bash
cd data-analysis
./run_analytics.sh
```

---

## What Each Script Does:

### 1. **hotspot_detection.py**
**Finds:** Geographical areas with high crime concentration  
**Method:** DBSCAN clustering (groups incidents within ~1km)  
**Output:** `hotspot_analysis` table  
**Example:** "Westlands Market: 47 robberies, avg severity 3.2"

### 2. **temporal_analysis.py**
**Finds:** High-risk time periods  
**Method:** Groups by day-of-week + hour-of-day  
**Output:** `temporal_patterns` table  
**Example:** "Friday 18:00-19:00: 23 robberies (high risk)"

### 3. **crime_correlation.py**
**Finds:** Patterns suggesting organized crime  
**Method:** Multi-dimensional clustering (location + time)  
**Output:** `crime_correlations` table  
**Example:** "5 robberies, same pattern, likely organized"

---

## Database Tables Created

When you run the scripts, they automatically create these tables:

### `hotspot_analysis`
```sql
CREATE TABLE hotspot_analysis (
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
);
```

### `temporal_patterns`
```sql
CREATE TABLE temporal_patterns (
    id SERIAL PRIMARY KEY,
    day_of_week INT,
    hour_of_day INT,
    category TEXT,
    incident_count INT,
    avg_severity NUMERIC(5,2),
    risk_level TEXT,
    last_updated TIMESTAMP
);
```

### `crime_correlations`
```sql
CREATE TABLE crime_correlations (
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
);
```

---

## Next Steps

### 1. Add Go API Queries
Add to `backend/db/query/analytics.sql`:
```sql
-- name: GetHotspots :many
SELECT * FROM hotspot_analysis
ORDER BY avg_severity DESC, incident_count DESC;

-- name: GetTemporalPatterns :many
SELECT * FROM temporal_patterns
WHERE risk_level IN ('high', 'medium')
ORDER BY day_of_week, hour_of_day;

-- name: GetCrimeCorrelations :many
SELECT * FROM crime_correlations
WHERE is_likely_organized = true
ORDER BY confidence_score DESC;
```

Then run: `cd backend && sqlc generate`

### 2. Create Go API Handlers
See `README.md` for full implementation details

### 3. Schedule Cron Job
```bash
# Edit crontab
crontab -e

# Run every 6 hours
0 */6 * * * cd /home/davi/m_kenya/data-analysis && ./run_analytics.sh >> /var/log/m_kenya_analytics.log 2>&1
```

---

## Testing

Before running on real data, test with sample data:

```bash
cd data-analysis
source venv/bin/activate

# Test database connection
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB:', os.getenv('DB_CONNECTION')[:50])"

# Run hotspot detection (requires at least 5 reports with location)
python hotspot_detection.py
```

---

## Architecture Summary

```
User Reports → Go API → PostgreSQL (reports table)
                            ↓
Python Scripts (every 6 hours) → Read reports
                            ↓
                     Run Analytics (clustering, patterns)
                            ↓
                     Write to analytics tables
                            ↓
Go API → Read analytics tables → Serve to Next.js
                            ↓
                     Next.js Dashboard displays results
```

**Python never talks to users** - just reads/writes database! 🎯

