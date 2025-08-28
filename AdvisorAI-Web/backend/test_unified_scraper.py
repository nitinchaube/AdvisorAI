"""
Test script for the unified GitHub scraper
Tests both New Grad and Summer Internships repositories
"""

import logging
from github_jobs_unified_scraper import UnifiedGitHubScraper
import pandas as pd
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_unified_scraper():
    print("🚀 Testing Unified GitHub Scraper")
    print("=" * 50)
    
    scraper = UnifiedGitHubScraper()
    
    # Test both repositories
    print("\n📥 Running unified scraper for both repositories...")
    scraper.scrape_all_repositories()
    
    # Check results for both CSV files
    for repo_key, repo_config in scraper.repositories.items():
        csv_file = repo_config['csv_file']
        repo_name = repo_config['name']
        
        print(f"\n{'='*60}")
        print(f"📊 Results for {repo_name}")
        print(f"{'='*60}")
        
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            print(f"✅ CSV created with {len(df)} total jobs")
            
            if len(df) > 0:
                print(f"\n📋 Sample jobs from {repo_name}:")
                print("-" * 50)
                
                for i, (_, row) in enumerate(df.head(3).iterrows()):
                    print(f"\n🔹 Job {i+1}:")
                    print(f"   Title: {row['Position Title']}")
                    print(f"   Company: {row['Company']}")
                    print(f"   Location: {row['Location']}")
                    print(f"   Industry: {row['Company Industry']}")
                    print(f"   Type: {row['Qualifications']}")
                    print(f"   Apply: {row['Apply'][:50]}..." if len(str(row['Apply'])) > 50 else f"   Apply: {row['Apply']}")
                
                # Show statistics
                print(f"\n📊 Category Statistics for {repo_name}:")
                print("-" * 40)
                
                industry_counts = df['Company Industry'].value_counts()
                for industry, count in industry_counts.items():
                    print(f"   {industry}: {count} jobs")
                
                # Data completeness
                print(f"\n📈 Data Completeness for {repo_name}:")
                for col in df.columns:
                    non_empty = df[col].notna().sum()
                    percentage = (non_empty / len(df)) * 100
                    print(f"   {col}: {percentage:.1f}%")
            
            else:
                print(f"⚠️ CSV file for {repo_name} is empty")
        else:
            print(f"❌ CSV file for {repo_name} was not created")
    
    # Combined statistics
    print(f"\n{'='*60}")
    print("🎯 Combined Statistics")
    print(f"{'='*60}")
    
    total_jobs = 0
    total_categories = {}
    
    for repo_key, repo_config in scraper.repositories.items():
        csv_file = repo_config['csv_file']
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            total_jobs += len(df)
            
            industry_counts = df['Company Industry'].value_counts()
            for industry, count in industry_counts.items():
                total_categories[industry] = total_categories.get(industry, 0) + count
    
    print(f"Total jobs across both repositories: {total_jobs}")
    print(f"\nCombined category breakdown:")
    for industry, count in sorted(total_categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {industry}: {count} jobs")
    
    print(f"\n🎉 Unified scraper test completed!")

if __name__ == "__main__":
    test_unified_scraper()
