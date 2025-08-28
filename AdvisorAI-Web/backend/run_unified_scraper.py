#!/usr/bin/env python3
"""
Unified runner script for GitHub jobs scraper
Handles both New Grad Positions and Summer 2026 Internships

Usage:
    python run_unified_scraper.py --once           # Scrape both repositories once
    python run_unified_scraper.py --new-grad       # Scrape only new grad jobs
    python run_unified_scraper.py --internships    # Scrape only summer internships
    python run_unified_scraper.py --schedule       # Use schedule library
    python run_unified_scraper.py                  # Continuous mode (default)
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_jobs_unified_scraper import main

if __name__ == "__main__":
    main()
