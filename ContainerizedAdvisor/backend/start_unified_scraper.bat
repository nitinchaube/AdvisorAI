@echo off
echo Starting Unified GitHub Jobs Scraper...
echo Scrapes both New Grad Positions and Summer 2026 Internships
echo.
echo Choose an option:
echo 1. Scrape both repositories once
echo 2. Scrape both repositories continuously (every 2 hours)
echo 3. Scrape only New Grad Positions
echo 4. Scrape only Summer 2026 Internships
echo 5. Fix categories in both CSV files
echo 6. Fix categories in New Grad CSV only
echo 7. Fix categories in Internships CSV only
echo 8. Test unified scraper
echo.
set /p choice="Enter your choice (1-8): "

if %choice%==1 (
    echo Scraping both repositories once...
    python run_unified_scraper.py --once
) else if %choice%==2 (
    echo Starting continuous scraping for both repositories (every 2 hours)...
    echo Press Ctrl+C to stop
    python run_unified_scraper.py
) else if %choice%==3 (
    echo Scraping New Grad Positions only...
    python run_unified_scraper.py --new-grad
) else if %choice%==4 (
    echo Scraping Summer 2026 Internships only...
    python run_unified_scraper.py --internships
) else if %choice%==5 (
    echo Fixing categories in both CSV files...
    python github_jobs_unified_scraper.py --fix-categories
) else if %choice%==6 (
    echo Fixing categories in New Grad CSV only...
    python github_jobs_unified_scraper.py --fix-new-grad
) else if %choice%==7 (
    echo Fixing categories in Internships CSV only...
    python github_jobs_unified_scraper.py --fix-internships
) else if %choice%==8 (
    echo Testing unified scraper...
    python test_unified_scraper.py
) else (
    echo Invalid choice. Scraping both repositories once by default...
    python run_unified_scraper.py --once
)

pause
