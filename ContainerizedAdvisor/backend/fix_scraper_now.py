#!/usr/bin/env python3
"""
Quick fix script to resolve scraper update issues immediately
"""

import os
import sys
import shutil
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("🔧 Job Scraper Quick Fix")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists('github_jobs_unified_scraper.py'):
        print("❌ Error: Please run this script from the AdvisorAI-Web/backend directory")
        sys.exit(1)
    
    # Import the scraper
    try:
        from github_jobs_unified_scraper import UnifiedGitHubScraper
        print("✅ Successfully imported scraper")
    except ImportError as e:
        print(f"❌ Error importing scraper: {e}")
        sys.exit(1)
    
    # Initialize scraper
    scraper = UnifiedGitHubScraper()
    
    print("\n📊 Current Status:")
    for repo_key, repo_config in scraper.repositories.items():
        csv_file = repo_config['csv_file']
        repo_name = repo_config['name']
        
        if os.path.exists(csv_file):
            try:
                import pandas as pd
                df = pd.read_csv(csv_file)
                file_age = datetime.now().timestamp() - os.path.getmtime(csv_file)
                age_hours = file_age / 3600
                print(f"  {repo_name}: {len(df)} jobs, {age_hours:.1f} hours old")
            except Exception as e:
                print(f"  {repo_name}: ❌ Error reading file - {e}")
        else:
            print(f"  {repo_name}: ❌ File missing")
    
    # Ask user what to do
    print("\n🎯 Recommended Actions:")
    print("1. Force refresh all data (recommended if you haven't run scraper recently)")
    print("2. Run single scrape to add new jobs")
    print("3. Test scraper connectivity only")
    print("4. Exit without changes")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(0)
    
    if choice == "1":
        print("\n🔄 Performing force refresh...")
        print("This will backup existing data and fetch fresh job listings.")
        
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm == 'y':
            try:
                scraper.refresh_csv_data(force_refresh=True)
                print("✅ Force refresh completed!")
            except Exception as e:
                print(f"❌ Error during refresh: {e}")
        else:
            print("❌ Cancelled")
    
    elif choice == "2":
        print("\n📥 Running single scrape...")
        try:
            scraper.scrape_all_repositories()
            print("✅ Single scrape completed!")
        except Exception as e:
            print(f"❌ Error during scrape: {e}")
    
    elif choice == "3":
        print("\n🌐 Testing connectivity...")
        for repo_key, repo_config in scraper.repositories.items():
            repo_name = repo_config['name']
            url = repo_config['url']
            print(f"  Testing {repo_name}...")
            
            try:
                content = scraper.fetch_readme_content(url, repo_name)
                if content and len(content) > 1000:
                    print(f"    ✅ Connected successfully ({len(content)} chars)")
                else:
                    print(f"    ⚠️  Connected but got minimal content")
            except Exception as e:
                print(f"    ❌ Connection failed: {e}")
    
    elif choice == "4":
        print("👋 Exiting without changes")
    
    else:
        print("❌ Invalid choice")
    
    print("\n📝 Next Steps:")
    print("- Monitor the scraper log: tail -f unified_github_scraper.log")
    print("- Run continuous scraping: python github_jobs_unified_scraper.py")
    print("- Check web interface to see if new jobs appear")
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
