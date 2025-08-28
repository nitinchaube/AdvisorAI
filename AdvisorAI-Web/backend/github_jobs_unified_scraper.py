"""
Unified GitHub Jobs Scraper
Scrapes both New Grad Positions and Summer 2026 Internships repositories
Saves data to separate CSV files with the same structure
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import logging
from datetime import datetime
import os
import pandas as pd
import schedule
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_github_scraper.log'),
        logging.StreamHandler()
    ]
)

class UnifiedGitHubScraper:
    def __init__(self):
        # Repository configurations
        self.repositories = {
            'new_grad': {
                'name': 'New Grad Positions',
                'url': 'https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md',
                'csv_file': 'jobs.csv',
                'hire_time': '2026',
                'graduate_time': '2025-2026',
                'job_type': 'New graduate position'
            },
            'internships': {
                'name': 'Summer 2026 Internships',
                'url': 'https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md',
                'csv_file': 'internships.csv',
                'hire_time': 'Summer 2026',
                'graduate_time': '2025-2026',
                'job_type': 'Summer 2026 internship'
            }
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Setup CSV files
        for repo_key, repo_config in self.repositories.items():
            self.setup_csv_headers(repo_config['csv_file'])
        
    def setup_csv_headers(self, csv_filename):
        """Initialize CSV file with headers (only if file doesn't exist)"""
        headers = [
            'Position Title', 'Date', 'Apply', 'Work Model', 'Location', 
            'Company', 'Hire Time', 'Graduate Time', 'Company Industry', 
            'Company Size', 'Salary', 'Qualifications'
        ]
        
        if not os.path.exists(csv_filename):
            with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
            logging.info(f"Created new CSV file: {csv_filename}")

    def fetch_readme_content(self, url, repo_name):
        """Fetch the README.md content from GitHub"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            logging.info(f"Successfully fetched README.md from {repo_name}")
            return response.text
        except Exception as e:
            logging.error(f"Failed to fetch README content from {repo_name}: {e}")
            return None

    def parse_html_tables(self, content, repo_config):
        """Parse job listings from HTML tables in the README"""
        jobs = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Parse HTML content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all HTML tables
        tables = soup.find_all('table')
        logging.info(f"Found {len(tables)} HTML tables in {repo_config['name']}")
        
        for i, table in enumerate(tables):
            logging.info(f"Processing table {i+1} from {repo_config['name']}")
            
            # Find the section this table belongs to
            section_name = self.find_section_for_table(table, content)
            
            # Get all rows from the table
            rows = table.find_all('tr')
            logging.info(f"Table {i+1} has {len(rows)} rows")
            
            # Skip header row (first row)
            for j, row in enumerate(rows[1:], 1):
                try:
                    job_data = self.parse_html_row(row, section_name, current_date, repo_config)
                    if job_data and self.is_valid_job(job_data):
                        jobs.append(job_data)
                        if j <= 3:  # Log first few successful extractions
                            logging.info(f"Extracted: {job_data['Position Title']} at {job_data['Company']}")
                    elif j <= 5:  # Log first few failures for debugging
                        logging.debug(f"Row {j} failed validation or parsing")
                except Exception as e:
                    if j <= 5:  # Only log first few errors
                        logging.debug(f"Error parsing row {j}: {e}")
        
        logging.info(f"Total jobs extracted from {repo_config['name']}: {len(jobs)}")
        return jobs

    def find_section_for_table(self, table, content):
        """Find which section a table belongs to"""
        # Convert table to string to find its position
        table_str = str(table)[:200]
        
        # Find the position of this table in the content
        table_pos = content.find(table_str[:100])
        if table_pos == -1:
            # Try with table text content if HTML search fails
            table_text = table.get_text()[:100]
            table_pos = content.find(table_text)
        
        if table_pos == -1:
            # Fallback: try to identify from job titles in the table
            return self.identify_section_from_jobs(table)
        
        # Look backwards from table position to find the nearest section header
        content_before = content[:table_pos]
        
        # Section patterns for both repositories
        section_patterns = [
            # New Grad repository patterns
            (r'## 💻 Software Engineering New Grad Roles', 'Software Engineering'),
            (r'## 🤖 Data Science, AI & Machine Learning New Grad Roles', 'Data Science'),
            (r'## 📈 Quantitative Finance New Grad Roles', 'Quantitative Finance'),
            (r'## 🔧 Hardware Engineering New Grad Roles', 'Hardware Engineering'),
            (r'## 📱 Product Management New Grad Roles', 'Product Management'),
            (r'## 💼 Other New Grad Roles', 'Other'),
            # Internships repository patterns
            (r'## 💻 Software Engineering Internship Roles', 'Software Engineering'),
            (r'## 🤖 Data Science, AI & Machine Learning Internship Roles', 'Data Science'),
            (r'## 📈 Quantitative Finance Internship Roles', 'Quantitative Finance'),
            (r'## 🔧 Hardware Engineering Internship Roles', 'Hardware Engineering'),
            (r'## 📱 Product Management Internship Roles', 'Product Management'),
            (r'## 💼 Other Internship Roles', 'Other'),
            # Generic fallback patterns
            (r'## 💻 Software Engineering', 'Software Engineering'),
            (r'## 🤖 Data Science', 'Data Science'),
            (r'## 📈 Quantitative Finance', 'Quantitative Finance'),
            (r'## 🔧 Hardware Engineering', 'Hardware Engineering'),
            (r'## 📱 Product Management', 'Product Management'),
            (r'## 💼 Other', 'Other')
        ]
        
        latest_match = None
        latest_pos = -1
        
        for pattern, name in section_patterns:
            matches = list(re.finditer(pattern, content_before))
            if matches:
                last_match = matches[-1]
                if last_match.start() > latest_pos:
                    latest_pos = last_match.start()
                    latest_match = name
        
        return latest_match or self.identify_section_from_jobs(table)

    def identify_section_from_jobs(self, table):
        """Identify section based on job titles in the table"""
        rows = table.find_all('tr')
        job_titles = []
        
        # Extract job titles from the table
        for row in rows[1:6]:  # Check first 5 job rows
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:  # Need at least company and role columns
                role_cell = cells[1]
                if role_cell:
                    title = self.extract_text_from_cell(role_cell).lower()
                    job_titles.append(title)
        
        # Analyze job titles to determine category
        all_titles = ' '.join(job_titles)
        return self.classify_job_by_title_content(all_titles)

    def classify_job_by_title_content(self, title_content):
        """Classify job based on title content"""
        title_lower = title_content.lower()
        
        # Data Science & AI keywords
        if any(keyword in title_lower for keyword in [
            'data scientist', 'machine learning', 'ai engineer', 'ml engineer',
            'data engineer', 'data analyst', 'research scientist', 'nlp', 
            'computer vision', 'artificial intelligence', 'deep learning',
            'analytics engineer', 'data science', 'ml ', 'ai ', 'data mining',
            'business intelligence', 'statistician', 'research engineer'
        ]):
            return 'Data Science'
        
        # Hardware Engineering keywords
        elif any(keyword in title_lower for keyword in [
            'hardware', 'electrical engineer', 'chip', 'semiconductor', 'fpga',
            'asic', 'circuit', 'embedded', 'firmware', 'systems engineer',
            'rf engineer', 'analog', 'digital design', 'vlsi', 'eda',
            'physical design', 'verification engineer', 'test engineer'
        ]):
            return 'Hardware Engineering'
        
        # Quantitative Finance keywords
        elif any(keyword in title_lower for keyword in [
            'quant', 'quantitative', 'trading', 'risk', 'portfolio',
            'derivatives', 'financial engineer', 'algorithmic trading',
            'trader', 'finance', 'investment', 'capital markets',
            'fixed income', 'equity', 'commodities', 'credit'
        ]):
            return 'Quantitative Finance'
        
        # Product Management keywords
        elif any(keyword in title_lower for keyword in [
            'product manager', 'product owner', 'pm ', 'product marketing',
            'product analyst', 'product strategy', 'product specialist',
            'program manager', 'project manager', 'product operations'
        ]):
            return 'Product Management'
        
        # Software Engineering keywords (most common, so check after others)
        elif any(keyword in title_lower for keyword in [
            'software engineer', 'developer', 'programmer', 'backend', 'frontend',
            'full stack', 'web developer', 'mobile developer', 'devops',
            'software developer', 'application developer', 'systems developer',
            'platform engineer', 'cloud engineer', 'site reliability',
            'infrastructure engineer', 'automation engineer', 'swe'
        ]):
            return 'Software Engineering'
        
        # Other categories
        else:
            return 'Other'

    def parse_html_row(self, row, section_name, current_date, repo_config):
        """Parse a single HTML table row into job data"""
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < 4:  # Need at least company, role, location, application
            return None
        
        # Initialize job data
        job_data = {
            'Position Title': '',
            'Date': current_date,
            'Apply': '',
            'Work Model': '',
            'Location': '',
            'Company': '',
            'Hire Time': repo_config['hire_time'],
            'Graduate Time': repo_config['graduate_time'],
            'Company Industry': section_name,
            'Company Size': '',
            'Salary': '',
            'Qualifications': repo_config['job_type']
        }
        
        try:
            # Extract data from cells: Company | Role | Location | Application | Age
            company_cell = cells[0] if len(cells) > 0 else None
            role_cell = cells[1] if len(cells) > 1 else None
            location_cell = cells[2] if len(cells) > 2 else None
            application_cell = cells[3] if len(cells) > 3 else None
            
            # Extract company name
            if company_cell:
                company_text = self.extract_text_from_cell(company_cell)
                # Handle continuation rows (↳)
                if company_text.strip() == '↳' or not company_text.strip():
                    job_data['Company'] = 'Previous Company'  # Will be handled later
                else:
                    job_data['Company'] = self.clean_text(company_text)
            
            # Extract position title
            if role_cell:
                job_data['Position Title'] = self.clean_text(self.extract_text_from_cell(role_cell))
            
            # Extract location
            if location_cell:
                location_text = self.extract_text_from_cell(location_cell)
                job_data['Location'] = self.clean_text(location_text)
                
                # Determine work model
                location_lower = location_text.lower()
                if 'remote' in location_lower:
                    job_data['Work Model'] = 'Remote'
                elif 'hybrid' in location_lower:
                    job_data['Work Model'] = 'Hybrid'
                elif 'locations' in location_lower or '</br>' in location_text or len(location_text) > 50:
                    job_data['Work Model'] = 'Multiple Locations'
                else:
                    job_data['Work Model'] = 'On-site'
            
            # Extract application link
            if application_cell:
                links = application_cell.find_all('a', href=True)
                if links:
                    # Get the first application link (not the Simplify link)
                    for link in links:
                        href = link.get('href', '')
                        if href and not 'simplify.jobs' in href:
                            job_data['Apply'] = href
                            break
                    
                    # If no non-Simplify link found, use the first one
                    if not job_data['Apply'] and links:
                        job_data['Apply'] = links[0].get('href', '')
                
                # Check for closed jobs
                if '🔒' in str(application_cell):
                    job_data['Apply'] = 'Closed'
            
            # Extract additional metadata
            self.extract_metadata(job_data)
            
            # Override section-based industry with title-based classification for better accuracy
            job_data['Company Industry'] = self.classify_job_by_title(job_data['Position Title'])
            
        except Exception as e:
            logging.debug(f"Error parsing HTML row: {e}")
            return None
        
        return job_data

    def extract_text_from_cell(self, cell):
        """Extract clean text from HTML cell, preserving line breaks"""
        if not cell:
            return ''
        
        # Replace <br> tags with spaces
        for br in cell.find_all(['br', 'BR']):
            br.replace_with(' ')
        
        # Get text content
        text = cell.get_text(separator=' ', strip=True)
        return text

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ''
        
        # Remove special symbols and emojis
        text = re.sub(r'[🔥🛂🇺🇸🔒🎓↳]', '', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def classify_job_by_title(self, title):
        """Classify job into industry category based on position title"""
        if not title:
            return 'Other'
        
        title_lower = title.lower()
        
        # Data Science & AI keywords
        if any(keyword in title_lower for keyword in [
            'data scientist', 'machine learning', 'ai engineer', 'ml engineer',
            'data engineer', 'data analyst', 'research scientist', 'nlp', 
            'computer vision', 'artificial intelligence', 'deep learning',
            'analytics engineer', 'data science', 'ml ', 'ai ', 'data mining',
            'business intelligence', 'statistician', 'research engineer'
        ]):
            return 'Data Science'
        
        # Hardware Engineering keywords
        elif any(keyword in title_lower for keyword in [
            'hardware', 'electrical engineer', 'chip', 'semiconductor', 'fpga',
            'asic', 'circuit', 'embedded', 'firmware', 'systems engineer',
            'rf engineer', 'analog', 'digital design', 'vlsi', 'eda',
            'physical design', 'verification engineer', 'test engineer'
        ]):
            return 'Hardware Engineering'
        
        # Quantitative Finance keywords
        elif any(keyword in title_lower for keyword in [
            'quant', 'quantitative', 'trading', 'risk', 'portfolio',
            'derivatives', 'financial engineer', 'algorithmic trading',
            'trader', 'finance', 'investment', 'capital markets',
            'fixed income', 'equity', 'commodities', 'credit'
        ]):
            return 'Quantitative Finance'
        
        # Product Management keywords
        elif any(keyword in title_lower for keyword in [
            'product manager', 'product owner', 'pm ', 'product marketing',
            'product analyst', 'product strategy', 'product specialist',
            'program manager', 'project manager', 'product operations'
        ]):
            return 'Product Management'
        
        # Software Engineering keywords (most common, so check after others)
        elif any(keyword in title_lower for keyword in [
            'software engineer', 'developer', 'programmer', 'backend', 'frontend',
            'full stack', 'web developer', 'mobile developer', 'devops',
            'software developer', 'application developer', 'systems developer',
            'platform engineer', 'cloud engineer', 'site reliability',
            'infrastructure engineer', 'automation engineer', 'swe'
        ]):
            return 'Software Engineering'
        
        # Other categories
        elif any(keyword in title_lower for keyword in [
            'security engineer', 'cybersecurity', 'network engineer',
            'consultant', 'analyst', 'coordinator', 'specialist', 'associate',
            'operations', 'support', 'sales', 'marketing', 'hr', 'legal'
        ]):
            return 'Other'
        
        # Default fallback for any engineer role
        elif 'engineer' in title_lower:
            return 'Software Engineering'
        else:
            return 'Other'

    def extract_metadata(self, job_data):
        """Extract additional metadata from job data"""
        title = job_data['Position Title'].lower()
        company = job_data['Company'].lower()
        
        # Determine company size
        large_companies = [
            'google', 'apple', 'amazon', 'microsoft', 'meta', 'facebook',
            'netflix', 'tesla', 'nvidia', 'oracle', 'salesforce', 'adobe',
            'intel', 'ibm', 'uber', 'spotify', 'airbnb', 'bytedance', 'tiktok',
            'fidelity', 'jpmorgan', 'goldman sachs', 'morgan stanley', 'bill',
            'caterpillar', 'disney', 'usaa'
        ]
        
        medium_companies = [
            'stripe', 'square', 'dropbox', 'zoom', 'slack', 'datadog',
            'snowflake', 'palantir', 'coinbase', 'robinhood', 'newrez',
            'tower research', 'imc trading', 'scanline vfx', 'commure',
            'abridge', 'valon'
        ]
        
        if any(large_comp in company for large_comp in large_companies):
            job_data['Company Size'] = '10000+'
        elif any(medium_comp in company for medium_comp in medium_companies):
            job_data['Company Size'] = '1000-10000'
        else:
            job_data['Company Size'] = '100-1000'
        
        # Update qualifications based on title and context
        if 'advanced degree' in title or 'phd' in title or 'masters' in title:
            job_data['Qualifications'] = f"{job_data['Qualifications']} - Advanced degree required"
        elif 'intern' in title:
            job_data['Qualifications'] = f"{job_data['Qualifications']} position"
        else:
            job_data['Qualifications'] = f"{job_data['Qualifications']}"

    def is_valid_job(self, job_data):
        """Validate extracted job data"""
        # Must have essential fields
        if not job_data.get('Position Title') or len(job_data['Position Title'].strip()) < 3:
            return False
        
        if not job_data.get('Company') or job_data['Company'] == 'Previous Company':
            return False
        
        # Filter out non-job content
        title_lower = job_data['Position Title'].lower()
        invalid_keywords = ['back to top', 'contributing', 'legend', 'about', 'company', 'role', 'location']
        
        if any(keyword in title_lower for keyword in invalid_keywords):
            return False
        
        return True

    def save_to_csv(self, jobs, csv_filename, repo_name):
        """Save jobs to CSV file by completely replacing the file with fresh data"""
        if not jobs:
            logging.warning(f"No jobs to save for {repo_name}")
            return
        
        # Create backup of existing file if it exists
        if os.path.exists(csv_filename):
            backup_filename = f"{csv_filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                shutil.copy2(csv_filename, backup_filename)
                logging.info(f"Created backup: {backup_filename}")
            except Exception as e:
                logging.warning(f"Failed to create backup: {e}")
        
        # Remove duplicates within the new data set (in case source has duplicates)
        unique_jobs = []
        seen_jobs = set()
        
        for job in jobs:
            # Create identifier for deduplication within this batch
            title = str(job['Position Title']).strip().lower()
            company = str(job['Company']).strip().lower()
            location = str(job['Location']).strip().lower()
            identifier = f"{title}|{company}|{location}"
            
            if identifier not in seen_jobs:
                unique_jobs.append(job)
                seen_jobs.add(identifier)
        
        # Completely replace the CSV file with fresh data
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=[
                    'Position Title', 'Date', 'Apply', 'Work Model', 'Location',
                    'Company', 'Hire Time', 'Graduate Time', 'Company Industry',
                    'Company Size', 'Salary', 'Qualifications'
                ])
                writer.writeheader()
                writer.writerows(unique_jobs)
            
            removed_duplicates = len(jobs) - len(unique_jobs)
            logging.info(f"Completely replaced {csv_filename} with {len(unique_jobs)} jobs from {repo_name}")
            if removed_duplicates > 0:
                logging.info(f"Removed {removed_duplicates} duplicate jobs within the source data")
            
            # Log statistics
            self.log_statistics(unique_jobs, repo_name)
            
        except Exception as e:
            logging.error(f"Error writing to {csv_filename}: {e}")
            # Try to restore from backup if write failed
            backup_files = [f for f in os.listdir('.') if f.startswith(f"{csv_filename}.backup_")]
            if backup_files:
                latest_backup = sorted(backup_files)[-1]
                try:
                    shutil.copy2(latest_backup, csv_filename)
                    logging.info(f"Restored from backup: {latest_backup}")
                except Exception as restore_error:
                    logging.error(f"Failed to restore from backup: {restore_error}")

    def log_statistics(self, jobs, repo_name):
        """Log job statistics"""
        if not jobs:
            return
        
        # Count by industry
        industry_counts = {}
        for job in jobs:
            industry = job.get('Company Industry', 'Unknown')
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        logging.info(f"New jobs from {repo_name} by category:")
        for industry, count in sorted(industry_counts.items(), key=lambda x: x[1], reverse=True):
            logging.info(f"  {industry}: {count} jobs")

    def fix_existing_categories(self, repo_key=None):
        """Fix categories in existing CSV files"""
        repos_to_fix = [repo_key] if repo_key else self.repositories.keys()
        
        for repo_key in repos_to_fix:
            repo_config = self.repositories[repo_key]
            csv_filename = repo_config['csv_file']
            repo_name = repo_config['name']
            
            if not os.path.exists(csv_filename):
                logging.warning(f"CSV file {csv_filename} does not exist, nothing to fix")
                continue
            
            logging.info(f"Fixing job categories in {csv_filename} ({repo_name})...")
            
            try:
                # Read existing CSV
                df = pd.read_csv(csv_filename)
                original_count = len(df)
                
                logging.info(f"Original categories in {original_count} jobs from {repo_name}:")
                original_counts = df['Company Industry'].value_counts()
                for category, count in original_counts.items():
                    logging.info(f"  {category}: {count}")
                
                # Fix categories based on job titles
                df['Company Industry'] = df['Position Title'].apply(self.classify_job_by_title)
                
                # Save updated CSV
                df.to_csv(csv_filename, index=False)
                
                logging.info(f"Updated categories for {repo_name}:")
                new_counts = df['Company Industry'].value_counts()
                for category, count in new_counts.items():
                    logging.info(f"  {category}: {count}")
                
                logging.info(f"Successfully updated {original_count} job categories in {csv_filename}")
                
            except Exception as e:
                logging.error(f"Error fixing categories in {csv_filename}: {e}")



    def scrape_repository(self, repo_key):
        """Scrape a specific repository"""
        repo_config = self.repositories[repo_key]
        
        logging.info(f"Starting scraping for {repo_config['name']}...")
        
        # Fetch README content
        content = self.fetch_readme_content(repo_config['url'], repo_config['name'])
        if not content:
            logging.error(f"Failed to fetch README content for {repo_config['name']}")
            return
        
        # Parse job listings
        jobs = self.parse_html_tables(content, repo_config)
        
        if jobs:
            logging.info(f"Successfully extracted {len(jobs)} jobs from {repo_config['name']}")
            self.save_to_csv(jobs, repo_config['csv_file'], repo_config['name'])
        else:
            logging.warning(f"No jobs extracted from {repo_config['name']}")

    def scrape_all_repositories(self):
        """Scrape both repositories"""
        logging.info("Starting unified scraping for both repositories...")
        
        for repo_key in self.repositories.keys():
            self.scrape_repository(repo_key)
            
        logging.info("Completed scraping both repositories")

    def run_continuous(self):
        """Run scraping continuously with 2-hour intervals"""
        logging.info("Starting continuous unified scraping (every 2 hours)")
        
        while True:
            try:
                self.scrape_all_repositories()
                logging.info("Waiting 2 hours before next scrape...")
                time.sleep(7200)  # 2 hours
            except KeyboardInterrupt:
                logging.info("Scraping stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in continuous scraping: {e}")
                logging.info("Waiting 30 minutes before retry...")
                time.sleep(1800)  # 30 minutes

    def run_scheduled(self):
        """Run scraping on schedule"""
        logging.info("Starting scheduled unified scraping (every 2 hours)")
        
        schedule.every(2).hours.do(self.scrape_all_repositories)
        
        # Run immediately
        self.scrape_all_repositories()
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """Main function"""
    scraper = UnifiedGitHubScraper()
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        scraper.run_scheduled()
    elif len(sys.argv) > 1 and sys.argv[1] == "--once":
        scraper.scrape_all_repositories()
    elif len(sys.argv) > 1 and sys.argv[1] == "--new-grad":
        scraper.scrape_repository('new_grad')
    elif len(sys.argv) > 1 and sys.argv[1] == "--internships":
        scraper.scrape_repository('internships')
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix-categories":
        scraper.fix_existing_categories()
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix-new-grad":
        scraper.fix_existing_categories('new_grad')
    elif len(sys.argv) > 1 and sys.argv[1] == "--fix-internships":
        scraper.fix_existing_categories('internships')
    else:
        scraper.run_continuous()

if __name__ == "__main__":
    main()
