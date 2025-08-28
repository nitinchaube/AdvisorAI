#!/usr/bin/env python3
"""
Test script to verify the scraper fixes are working properly
"""

import os
import sys
import pandas as pd
from datetime import datetime
import logging

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_jobs_unified_scraper import UnifiedGitHubScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_scraper_functionality():
    """Test the scraper functionality"""
    print("🧪 Testing Scraper Functionality")
    print("=" * 50)
    
    scraper = UnifiedGitHubScraper()
    
    # Test 1: Check CSV file configuration
    print("\n📁 Test 1: CSV File Configuration")
    for repo_key, repo_config in scraper.repositories.items():
        csv_file = repo_config['csv_file']
        repo_name = repo_config['name']
        print(f"  {repo_name}: {csv_file}")
        
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                print(f"    ✅ File exists with {len(df)} rows")
            except Exception as e:
                print(f"    ❌ Error reading file: {e}")
        else:
            print(f"    ⚠️  File does not exist")
    
    # Test 2: Check for stale backup files
    print("\n🗂️  Test 2: Checking for old CSV files")
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    for csv_file in csv_files:
        print(f"  Found: {csv_file}")
        try:
            df = pd.read_csv(csv_file)
            file_age = datetime.now().timestamp() - os.path.getmtime(csv_file)
            age_hours = file_age / 3600
            print(f"    {len(df)} rows, {age_hours:.1f} hours old")
        except Exception as e:
            print(f"    Error reading: {e}")
    
    # Test 3: Test duplicate detection logic
    print("\n🔍 Test 3: Testing Duplicate Detection")
    
    # Create sample job data
    sample_jobs = [
        {
            'Position Title': 'Software Engineer',
            'Company': 'Test Company',
            'Location': 'San Francisco, CA',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job1',
            'Work Model': 'On-site',
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Software Engineering',
            'Company Size': '1000-10000',
            'Salary': '',
            'Qualifications': 'New graduate position'
        },
        {
            'Position Title': 'Software Engineer',  # Exact duplicate
            'Company': 'Test Company',
            'Location': 'San Francisco, CA',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job2',  # Different URL
            'Work Model': 'On-site',
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Software Engineering',
            'Company Size': '1000-10000',
            'Salary': '',
            'Qualifications': 'New graduate position'
        },
        {
            'Position Title': 'Senior Software Engineer',  # Different title
            'Company': 'Test Company',
            'Location': 'San Francisco, CA',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job3',
            'Work Model': 'On-site',
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Software Engineering',
            'Company Size': '1000-10000',
            'Salary': '',
            'Qualifications': 'New graduate position'
        }
    ]
    
    # Test the duplicate detection
    test_csv = 'test_duplicates.csv'
    
    # First, save initial jobs
    scraper.save_to_csv(sample_jobs[:1], test_csv, 'Test Repository')
    
    # Then try to add duplicates and new jobs
    scraper.save_to_csv(sample_jobs, test_csv, 'Test Repository')
    
    # Check results
    if os.path.exists(test_csv):
        df = pd.read_csv(test_csv)
        print(f"  ✅ Test CSV created with {len(df)} rows")
        print(f"  Expected: 2 unique jobs (1 duplicate filtered)")
        
        # Cleanup
        os.remove(test_csv)
        print(f"  🧹 Cleaned up test file")
    
    # Test 4: Test repository connectivity
    print("\n🌐 Test 4: Testing Repository Connectivity")
    for repo_key, repo_config in scraper.repositories.items():
        repo_name = repo_config['name']
        url = repo_config['url']
        print(f"  Testing {repo_name}...")
        
        try:
            content = scraper.fetch_readme_content(url, repo_name)
            if content:
                print(f"    ✅ Successfully fetched content ({len(content)} chars)")
            else:
                print(f"    ❌ Failed to fetch content")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print("\n🎯 Test Summary")
    print("=" * 50)
    print("✅ Scraper functionality test completed")
    print("If you see mostly ✅ symbols above, the scraper should be working correctly.")
    print("\nTo run a fresh scrape, use:")
    print("  python github_jobs_unified_scraper.py --refresh")
    print("  python github_jobs_unified_scraper.py --once")

if __name__ == "__main__":
    test_scraper_functionality()
