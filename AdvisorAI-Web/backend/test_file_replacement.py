#!/usr/bin/env python3
"""
Test script to verify the complete file replacement approach works correctly
"""

import os
import sys
import csv
import pandas as pd
from datetime import datetime
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from github_jobs_unified_scraper import UnifiedGitHubScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_file_replacement():
    """Test the file replacement functionality"""
    print("🧪 Testing Complete File Replacement Approach")
    print("=" * 60)
    
    # Create test data
    test_csv = 'test_replacement.csv'
    
    # Sample jobs for testing
    sample_jobs_1 = [
        {
            'Position Title': 'Software Engineer',
            'Company': 'Test Company A',
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
            'Position Title': 'Data Scientist',
            'Company': 'Test Company B',
            'Location': 'New York, NY',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job2',
            'Work Model': 'Remote',
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Data Science',
            'Company Size': '100-1000',
            'Salary': '',
            'Qualifications': 'New graduate position'
        }
    ]
    
    sample_jobs_2 = [
        {
            'Position Title': 'Machine Learning Engineer',
            'Company': 'Test Company C',
            'Location': 'Seattle, WA',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job3',
            'Work Model': 'Hybrid',
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Data Science',
            'Company Size': '10000+',
            'Salary': '',
            'Qualifications': 'New graduate position'
        },
        {
            'Position Title': 'Product Manager',
            'Company': 'Test Company D',
            'Location': 'Austin, TX',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job4',
            'Work Model': 'On-site',
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Product Management',
            'Company Size': '1000-10000',
            'Salary': '',
            'Qualifications': 'New graduate position'
        },
        {
            'Position Title': 'Software Engineer',  # Same title/company as first batch (should replace)
            'Company': 'Test Company A',
            'Location': 'San Francisco, CA',
            'Date': '2025-08-27',
            'Apply': 'https://example.com/job5',  # Different URL
            'Work Model': 'Remote',  # Different work model
            'Hire Time': '2026',
            'Graduate Time': '2025-2026',
            'Company Industry': 'Software Engineering',
            'Company Size': '1000-10000',
            'Salary': '',
            'Qualifications': 'New graduate position'
        }
    ]
    
    scraper = UnifiedGitHubScraper()
    
    try:
        print("\n📝 Step 1: Creating initial CSV file with 2 jobs")
        scraper.save_to_csv(sample_jobs_1, test_csv, 'Test Repository')
        
        if os.path.exists(test_csv):
            df1 = pd.read_csv(test_csv)
            print(f"  ✅ Created file with {len(df1)} jobs")
            print(f"  📊 Jobs: {list(df1['Position Title'])}")
        
        print("\n🔄 Step 2: Completely replacing file with 3 different jobs")
        scraper.save_to_csv(sample_jobs_2, test_csv, 'Test Repository')
        
        if os.path.exists(test_csv):
            df2 = pd.read_csv(test_csv)
            print(f"  ✅ Replaced file with {len(df2)} jobs")
            print(f"  📊 Jobs: {list(df2['Position Title'])}")
            print(f"  🔍 Old jobs should be completely gone")
        
        print("\n🧹 Step 3: Checking for backup files")
        backup_files = [f for f in os.listdir('.') if f.startswith(f"{test_csv}.backup_")]
        if backup_files:
            print(f"  ✅ Found {len(backup_files)} backup file(s):")
            for backup in backup_files:
                print(f"    📁 {backup}")
        else:
            print("  ⚠️  No backup files found")
        
        print("\n🎯 Step 4: Verification")
        
        # Verify the file was completely replaced
        if os.path.exists(test_csv):
            df_final = pd.read_csv(test_csv)
            
            # Check that old jobs are gone
            old_jobs_present = any(job in list(df_final['Position Title']) for job in ['Data Scientist'])
            new_jobs_present = any(job in list(df_final['Position Title']) for job in ['Machine Learning Engineer', 'Product Manager'])
            
            if not old_jobs_present and new_jobs_present:
                print("  ✅ File replacement working correctly!")
                print("  ✅ Old jobs completely removed")
                print("  ✅ New jobs successfully added")
            else:
                print("  ❌ File replacement may have issues:")
                print(f"    Old jobs still present: {old_jobs_present}")
                print(f"    New jobs present: {new_jobs_present}")
        
        print(f"\n📈 Final Results:")
        print(f"  Total jobs in file: {len(df_final)}")
        print(f"  Companies: {list(df_final['Company'].unique())}")
        print(f"  Industries: {list(df_final['Company Industry'].unique())}")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test files...")
        if os.path.exists(test_csv):
            os.remove(test_csv)
            print(f"  🗑️  Removed {test_csv}")
        
        backup_files = [f for f in os.listdir('.') if f.startswith(f"{test_csv}.backup_")]
        for backup in backup_files:
            os.remove(backup)
            print(f"  🗑️  Removed {backup}")
    
    print("\n✅ Test completed!")
    print("\n📋 Summary of File Replacement Approach:")
    print("  • Each scrape completely replaces the CSV file")
    print("  • Automatic backup creation before replacement")
    print("  • No duplicate detection between old and new data")
    print("  • Deduplication only within the new dataset")
    print("  • Always fresh, current job listings")

if __name__ == "__main__":
    test_file_replacement()
