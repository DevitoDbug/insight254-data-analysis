# Insight254 Data Analytics

Python-based analytics pipeline for detecting crime patterns, hotspots, and predictions.

## Features

### 1. **Hotspot Detection** (`hotspot_detection.py`)
- Uses DBSCAN clustering to identify geographical crime hotspots
- Groups incidents within ~1km radius
- Calculates severity averages and primary crime categories
- **Output:** `hotspot_analysis` table

### 2. **Temporal Pattern Analysis** (`temporal_analysis.py`)
- Identifies high-risk time periods (day of week + hour)
- Analyzes 90 days of historical data
- Classifies risk levels (high/medium/low)
- **Output:** `temporal_patterns` table

### 3. **Crime Correlation** (`crime_correlation.py`)
- Detects patterns suggesting organized crime
- Multi-dimensional clustering (location + time)
- Calculates confidence scores
- **Output:** `crime_correlations` table

---

## Setup

### 1. Install Dependencies

```bash
cd data-analysis
pip install -r requirements.txt
```

Or use virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Database

Copy environment variables from backend:

```bash
cp ../backend/.env .env
```

Or create `.env` manually:

```env
DB_CONNECTION=postgresql://user:password@localhost:5432/m_kenya_db
```

### 3. Run Analytics

#### Manual Run:
```bash
# Run all analytics
./run_analytics.sh

# Or run individually
python3 hotspot_detection.py
python3 temporal_analysis.py
python3 crime_correlation.py
```

#### Scheduled Run (Cron):
```bash
# Edit crontab
crontab -e

# Add this line (runs every 6 hours)
0 */6 * * * cd /path/to/m_kenya/data-analysis && ./run_analytics.sh >> /var/log/m_kenya_analytics.log 2>&1
```

---

## Database Tables Created

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
    day_of_week INT,              -- 0=Sunday, 6=Saturday
    hour_of_day INT,               -- 0-23
    category TEXT,
    incident_count INT,
    avg_severity NUMERIC(5,2),
    risk_level TEXT,               -- 'high', 'medium', 'low'
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

## Go API Integration

Add these queries to `backend/db/query/analytics.sql`:

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

Run `sqlc generate` to create Go functions.

---

## Docker Deployment (Optional)

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run analytics every 6 hours
CMD ["sh", "-c", "while true; do ./run_analytics.sh; sleep 21600; done"]
```

### Add to docker-compose.yml
```yaml
analytics:
  build:
    context: ./data-analysis
  environment:
    - DB_CONNECTION=${DB_CONNECTION}
  depends_on:
    - postgres
```

---

## Monitoring

Check when analytics last ran:

```sql
SELECT 
    'hotspots' as table_name, 
    MAX(last_updated) as last_run
FROM hotspot_analysis
UNION ALL
SELECT 
    'patterns', 
    MAX(last_updated)
FROM temporal_patterns
UNION ALL
SELECT 
    'correlations', 
    MAX(last_updated)
FROM crime_correlations;
```

---

## Troubleshooting

**No hotspots detected:**
- Need at least 5 incidents within 1km radius
- Check if reports have latitude/longitude
- Adjust `eps` parameter in `hotspot_detection.py` (increase for larger radius)

**No temporal patterns:**
- Need at least 90 days of data
- Check if reports have `created_at` timestamps

**Database connection errors:**
- Verify `.env` file exists and has correct `DB_CONNECTION`
- Test connection: `psql $DB_CONNECTION`

---


