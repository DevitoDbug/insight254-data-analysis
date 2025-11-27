#!/bin/bash
# Run all analytics scripts

set -e  # Exit on error

echo "🚀 M-Kenya Analytics Pipeline Starting..."
echo "=========================================="
echo ""

# Check if .env exists (skip in Docker - env vars are passed directly)
if [ ! -f .env ] && [ -z "$DB_CONNECTION" ]; then
    echo "❌ Error: .env file not found and DB_CONNECTION not set"
    echo "   Please copy from backend: cp ../backend/.env .env"
    exit 1
fi

# Load .env if it exists (local development)
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded from .env"
fi

# Activate virtual environment (skip in Docker)
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found, using system Python"
fi
echo ""

# Run each analysis script
echo "1️⃣  Running Hotspot Detection..."
python hotspot_detection.py
echo ""

echo "2️⃣  Running Temporal Analysis..."
python temporal_analysis.py
echo ""

echo "3️⃣  Running Crime Correlation Analysis..."
python crime_correlation.py
echo ""

echo "=========================================="
echo "✅ Analytics pipeline complete!"
echo ""
echo "Results saved to PostgreSQL tables:"
echo "  - hotspot_analysis"
echo "  - temporal_patterns"
echo "  - crime_correlations"
echo ""
echo "Access via Go API:"
echo "  GET /api/analytics/hotspots"
echo "  GET /api/analytics/temporal-patterns"
echo "  GET /api/analytics/correlations"

