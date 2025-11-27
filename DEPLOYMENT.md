# Analytics Service - Deployment Guide

This guide covers deploying the M-Kenya Analytics Service to CapRover alongside the Go backend.

## Overview

The analytics service is a **separate microservice** that:

- Runs Python-based ML algorithms (hotspot detection, temporal analysis, crime correlation)
- Connects to the same PostgreSQL database as the Go backend
- Runs automatically every 6 hours
- Writes results to analytics tables for the Go API to serve

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Go Backend        │     │  Python Analytics   │
│   (Web + Worker)    │     │   Service           │
│                     │     │                     │
│ - Telegram Bot      │     │ - Hotspot Detection │
│ - REST API          │     │ - Temporal Analysis │
│ - Gemini AI         │     │ - Crime Correlation │
│ - Report Processing │     │ (Runs every 6 hours)│
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           └───────────┬───────────────┘
                       │
              ┌────────▼────────┐
              │   PostgreSQL    │
              │    Database     │
              └─────────────────┘
```

## Prerequisites

1. **CapRover server** with CLI installed
2. **PostgreSQL database** already set up (from backend deployment)
3. **GitHub repository** with Actions enabled

## Step 1: Create CapRover App

```bash
# Login to CapRover
caprover login

# Create the analytics app
caprover apps:create insight254-analytics

# Enable HTTPS (optional but recommended)
caprover domain add -n insight254-analytics -d analytics.yourdomain.com
caprover ssl enable -n insight254-analytics
```

## Step 2: Configure Environment Variables

In CapRover dashboard, go to your `insight254-analytics` app and add:

```env
DB_CONNECTION=postgresql://user:password@postgres-host:5432/m_kenya_db?sslmode=disable
```

**Important:** Use the **same database** as your backend services.

### Get Database Connection String

If you deployed PostgreSQL via CapRover:

```
postgresql://postgres:YOUR_PASSWORD@srv-captain--postgres:5432/m_kenya_db?sslmode=disable
```

Replace:

- `YOUR_PASSWORD` with your actual PostgreSQL password
- `srv-captain--postgres` with your PostgreSQL service name

## Step 3: Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

```
CAPROVER_SERVER=https://captain.yourdomain.com
CAPROVER_ANALYTICS_APP_NAME=insight254-analytics
CAPROVER_ANALYTICS_APP_TOKEN=<your-app-token>
```

### Get App Token

```bash
caprover app token -n insight254-analytics
```

## Step 4: Deploy via GitHub Actions

### Automatic Deployment

Push to `master` branch with changes to `data-analysis/` folder:

```bash
git add data-analysis/
git commit -m "Deploy analytics service"
git push origin master
```

GitHub Actions will:

1. ✅ Checkout code
2. ✅ Set up Python 3.11
3. ✅ Install dependencies
4. ✅ Validate Python scripts
5. ✅ Test database connection
6. ✅ Create deployment package
7. ✅ Deploy to CapRover

### Manual Deployment

From the `data-analysis/` directory:

```bash
# Create deployment tar
tar -czf deploy.tar.gz \
  hotspot_detection.py \
  temporal_analysis.py \
  crime_correlation.py \
  run_analytics.sh \
  requirements.txt \
  captain-definition \
  Dockerfile \
  .dockerignore

# Deploy to CapRover
caprover deploy -t ./deploy.tar.gz -n insight254-analytics
```

## Step 5: Verify Deployment

### Check Logs

```bash
caprover logs -n insight254-analytics -f
```

You should see:

```
🚀 M-Kenya Analytics Pipeline Starting...
==========================================

⚠️  Virtual environment not found, using system Python

1️⃣  Running Hotspot Detection...
✅ Processed X reports, found Y hotspots

2️⃣  Running Temporal Analysis...
✅ Analyzed Z temporal patterns

3️⃣  Running Crime Correlation Analysis...
✅ Identified W crime correlations

==========================================
✅ Analytics pipeline complete!
```

### Check Database

Connect to your PostgreSQL database and verify tables exist:

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('hotspot_analysis', 'temporal_patterns', 'crime_correlations');

-- Check data
SELECT COUNT(*) FROM hotspot_analysis;
SELECT COUNT(*) FROM temporal_patterns;
SELECT COUNT(*) FROM crime_correlations;

-- View most recent run
SELECT MAX(last_updated) FROM hotspot_analysis;
```

## Step 6: Configure Schedule (Optional)

The default schedule is **every 6 hours**. To change it:

### Option A: Modify Dockerfile

Edit `/home/davi/insight254/data-analysis/Dockerfile`:

```dockerfile
# Change sleep duration (in seconds)
# 3600 = 1 hour
# 21600 = 6 hours (default)
# 43200 = 12 hours
# 86400 = 24 hours

CMD ["sh", "-c", "while true; do ./run_analytics.sh; sleep 43200; done"]
```

### Option B: Use CapRover Cron (Advanced)

You can use an external cron service to trigger the analytics on-demand.

## Production Deployment Setup

### All Three Services Together

1. **insight254-web** (Go web server)

   - Port: 80/443
   - Dockerfile: `backend/Dockerfile.web`
   - GitHub Secret: `CAPROVER_WEB_APP_TOKEN`

2. **insight254-worker** (Go background worker)

   - No exposed port
   - Dockerfile: `backend/Dockerfile.worker`
   - GitHub Secret: `CAPROVER_WORKER_APP_TOKEN`

3. **insight254-analytics** (Python analytics)
   - No exposed port
   - Dockerfile: `data-analysis/Dockerfile`
   - GitHub Secret: `CAPROVER_ANALYTICS_APP_TOKEN`

All three connect to the **same PostgreSQL database**.

## Monitoring

### Check Analytics Health

```bash
# View logs
caprover logs -n insight254-analytics -f

# Check app status
caprover apps:list | grep analytics

# Restart if needed
caprover restart -n insight254-analytics
```

### Database Monitoring Query

```sql
-- Check when analytics last ran
SELECT
    'hotspots' as table_name,
    MAX(last_updated) as last_run,
    COUNT(*) as record_count
FROM hotspot_analysis
UNION ALL
SELECT
    'patterns',
    MAX(last_updated),
    COUNT(*)
FROM temporal_patterns
UNION ALL
SELECT
    'correlations',
    MAX(last_updated),
    COUNT(*)
FROM crime_correlations;
```

## Troubleshooting

### Service not running

```bash
# Check logs for errors
caprover logs -n insight254-analytics -f

# Restart the service
caprover restart -n insight254-analytics
```

### Database connection errors

- Verify `DB_CONNECTION` env var is set correctly
- Check if PostgreSQL is running
- Test connection from CapRover server:
  ```bash
  psql "$DB_CONNECTION"
  ```

### No data in analytics tables

- Check if reports exist in the `reports` table
- Need at least 5 reports for hotspot detection
- Need 90+ days of data for temporal patterns
- View Python script logs for error messages

### Analytics taking too long

- Check database indexes on `reports` table
- Consider adjusting the schedule (run less frequently)
- Monitor PostgreSQL performance

## Updating the Service

### Update Python Scripts

```bash
# Make changes to Python files
vim data-analysis/hotspot_detection.py

# Commit and push
git add data-analysis/
git commit -m "Update hotspot detection algorithm"
git push origin master
```

GitHub Actions will automatically deploy.

### Update Dependencies

```bash
# Update requirements.txt
vim data-analysis/requirements.txt

# Test locally
cd data-analysis
pip install -r requirements.txt
./run_analytics.sh

# Deploy
git add requirements.txt
git commit -m "Update Python dependencies"
git push origin master
```

## Local Testing

Before deploying, test locally:

```bash
cd data-analysis

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DB_CONNECTION=postgresql://user:password@localhost:5432/m_kenya_db
EOF

# Run analytics
./run_analytics.sh
```

## Rollback

If deployment fails:

```bash
# Check previous deployments
caprover logs -n insight254-analytics -f

# Redeploy previous version
git checkout <previous-commit>
git push -f origin master
```

## Next Steps

1. ✅ Deploy analytics service to CapRover
2. ✅ Verify it runs every 6 hours
3. ✅ Check database tables are populated
4. 🔄 Add Go API endpoints to serve analytics data
5. 🔄 Build frontend dashboard to visualize results
6. 🔄 Set up alerting for analytics failures

## Support

- **Logs**: `caprover logs -n insight254-analytics -f`
- **Database**: Check `hotspot_analysis`, `temporal_patterns`, `crime_correlations` tables
- **GitHub Actions**: Check Actions tab for deployment status

---

**Happy Deploying! 🚀**
