# Analytics Service - Quick Deploy Checklist ✅

Follow these steps to deploy the analytics service to CapRover.

## Prerequisites ✓

- [ ] CapRover server running
- [ ] PostgreSQL database deployed (from backend setup)
- [ ] Backend services (web + worker) already deployed
- [ ] GitHub repository connected

## Step 1: Create CapRover App (5 min)

```bash
# Login to CapRover
caprover login

# Create analytics app
caprover apps:create insight254-analytics
```

✅ App created: `insight254-analytics`

## Step 2: Configure Environment (2 min)

In CapRover Dashboard → Apps → `insight254-analytics` → App Configs → Environment Variables:

Add:

```
DB_CONNECTION=postgresql://user:password@srv-captain--postgres:5432/m_kenya_db?sslmode=disable
```

**Note:** Use the **same** `DB_CONNECTION` as your backend services.

✅ Environment variable added

## Step 3: Set Up GitHub Secrets (3 min)

Go to: `https://github.com/YOUR_USERNAME/insight254/settings/secrets/actions`

Add these secrets:

### Get App Token

```bash
caprover app token -n insight254-analytics
```

Copy the token and add:

- **Name:** `CAPROVER_ANALYTICS_APP_TOKEN`
- **Value:** `<paste-token-here>`

Also verify these exist (from backend setup):

- `CAPROVER_SERVER` (e.g., `https://captain.yourdomain.com`)

If `CAPROVER_ANALYTICS_APP_NAME` doesn't exist, add:

- **Name:** `CAPROVER_ANALYTICS_APP_NAME`
- **Value:** `insight254-analytics`

✅ GitHub secrets configured

## Step 4: Deploy! (2 min)

### Option A: Automatic (Recommended)

```bash
# Commit and push analytics files
git add data-analysis/
git commit -m "Add analytics service deployment"
git push origin master
```

GitHub Actions will automatically build and deploy.

### Option B: Manual

```bash
cd data-analysis

# Deploy to CapRover
caprover deploy -n insight254-analytics
```

✅ Deployment initiated

## Step 5: Verify (3 min)

### Check Deployment Status

**GitHub Actions:**

- Go to: `https://github.com/YOUR_USERNAME/insight254/actions`
- Click latest "Deploy Analytics Service" workflow
- Verify all steps passed ✅

**CapRover Logs:**

```bash
caprover logs -n insight254-analytics -f
```

You should see:

```
🚀 M-Kenya Analytics Pipeline Starting...
==========================================

1️⃣  Running Hotspot Detection...
✅ Processed X reports, found Y hotspots

2️⃣  Running Temporal Analysis...
✅ Analyzed Z temporal patterns

3️⃣  Running Crime Correlation Analysis...
✅ Identified W crime correlations

==========================================
✅ Analytics pipeline complete!
```

**Note:** First run might show "0 hotspots" if you don't have enough data yet. Need:

- At least 5 reports for hotspot detection
- 90+ days of data for temporal patterns

✅ Service running successfully

### Check Database

```sql
-- Connect to PostgreSQL
psql "$DB_CONNECTION"

-- Check tables exist
\dt

-- Verify analytics tables
SELECT table_name FROM information_schema.tables
WHERE table_name IN ('hotspot_analysis', 'temporal_patterns', 'crime_correlations');

-- Check data (might be empty on first run if not enough reports)
SELECT COUNT(*) FROM hotspot_analysis;
SELECT COUNT(*) FROM temporal_patterns;
SELECT COUNT(*) FROM crime_correlations;

-- View last run time
SELECT MAX(last_updated) FROM hotspot_analysis;
```

✅ Database tables created

## All Done! 🎉

Your analytics service is now:

- ✅ Running on CapRover
- ✅ Connected to PostgreSQL
- ✅ Executing every 6 hours
- ✅ Auto-deploying on push to master

## Next Steps

1. **Monitor**: Watch logs for first 24 hours

   ```bash
   caprover logs -n insight254-analytics -f
   ```

2. **Verify Data**: After 6+ hours, check database for results

   ```sql
   SELECT * FROM hotspot_analysis ORDER BY last_updated DESC LIMIT 5;
   ```

3. **API Integration**: The Go backend can now query these tables:

   - `hotspot_analysis`
   - `temporal_patterns`
   - `crime_correlations`

4. **Frontend**: Build dashboard to visualize the analytics data

## Troubleshooting

### Service not starting?

```bash
# Check logs
caprover logs -n insight254-analytics -f

# Restart
caprover restart -n insight254-analytics
```

### Database connection error?

- Verify `DB_CONNECTION` in CapRover app config
- Test connection: `psql "$DB_CONNECTION"`
- Check PostgreSQL is running

### No analytics data?

- Need at least 5 reports with lat/lng for hotspots
- Need 90+ days of data for temporal patterns
- Check `reports` table has data: `SELECT COUNT(*) FROM reports;`

### GitHub Actions failing?

- Check secrets are set correctly
- Verify app token: `caprover app token -n insight254-analytics`
- Check workflow file: `.github/workflows/deploy-analytics.yml`

## Configuration

### Change Schedule

Edit `data-analysis/Dockerfile`:

```dockerfile
# Current: Every 6 hours
CMD ["sh", "-c", "while true; do ./run_analytics.sh; sleep 21600; done"]

# Every 12 hours
CMD ["sh", "-c", "while true; do ./run_analytics.sh; sleep 43200; done"]

# Daily
CMD ["sh", "-c", "while true; do ./run_analytics.sh; sleep 86400; done"]
```

Push changes:

```bash
git add data-analysis/Dockerfile
git commit -m "Update analytics schedule"
git push origin master
```

### Manual Trigger

Force analytics to run immediately:

```bash
# SSH into CapRover container
caprover ssh -n insight254-analytics

# Run manually
./run_analytics.sh

# Exit
exit
```

## Monitoring Commands

```bash
# View all apps
caprover apps:list

# Check analytics status
caprover logs -n insight254-analytics --lines 100

# Restart if needed
caprover restart -n insight254-analytics

# View resource usage
# (Check in CapRover Dashboard)
```

## Documentation

- **Full Guide**: `DEPLOYMENT.md`
- **Project Overview**: `../DEPLOYMENT_SUMMARY.md`
- **Analytics Info**: `README.md`

---

**Your analytics service is live! 🚀**

Questions? Check the logs or review `DEPLOYMENT.md` for detailed troubleshooting.
