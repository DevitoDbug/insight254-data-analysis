# Data Analysis

Analytics pipeline for detecting crime hotspots, temporal patterns, and correlated incident clusters. Runs against the same Postgres database as the backend.

## Scripts

| Script | What it does | Output table |
|---|---|---|
| `hotspot_detection.py` | DBSCAN clustering on incident coordinates to find geographic hotspots | `hotspot_analysis` |
| `temporal_analysis.py` | Groups incidents by day/hour to classify high-risk time windows | `temporal_patterns` |
| `crime_correlation.py` | Multi-dimensional clustering (location + time) to flag likely organized activity | `crime_correlations` |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy the backend `.env` or create one with:

```
DB_CONNECTION=postgresql://user:password@localhost:5432/insight254_db
```

## Running

```bash
./run_analytics.sh          # all three
python3 hotspot_detection.py  # individually
```

For scheduled runs, add to cron:

```
0 */6 * * * cd /path/to/data-analysis && ./run_analytics.sh >> /var/log/analytics.log 2>&1
```
