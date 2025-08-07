#!/usr/bin/env python3
"""
Faculty data mapper - converts between MongoDB format and Admin Dashboard format
"""

import re
import json

def extract_email_from_text(text):
    """Extract email from text using regex"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""

def extract_phone_from_text(text):
    """Extract phone number from text using regex"""
    phone_pattern = r'\(\d{3}\)\s?\d{3}-\d{4}|\d{3}-\d{3}-\d{4}|\(\d{3}\)\s?\d{3}\s?\d{4}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ""

def extract_department_from_text(text):
    """Extract department from general info text"""
    # Look for common department indicators
    dept_patterns = [
        r'Stevens Institute of Technology.*?([A-Z][^,\n]*)',
        r'School of ([^,\n]*)',
        r'Department of ([^,\n]*)',
        r'College of ([^,\n]*)'
    ]
    
    for pattern in dept_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "Stevens Institute of Technology"

def extract_title_from_text(text):
    """Extract academic title from text"""
    title_patterns = [
        r'(Professor|Associate Professor|Assistant Professor)',
        r'(Director|Dean|Chair)',
        r'(Lecturer|Instructor)'
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return "Faculty"

def extract_office_from_text(text):
    """Extract office information from text"""
    # Look for room/office patterns
    office_patterns = [
        r'Room\s+(\d+[A-Z]?)',
        r'Office\s+(\d+[A-Z]?)',
        r'Building\s+([A-Z]+)\s+(\d+)'
    ]
    
    for pattern in office_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return ""

def mongo_faculty_to_admin_format(mongo_faculty):
    """Convert MongoDB faculty format to admin dashboard format"""
    general_info = mongo_faculty.get('general_info', '')
    research_info = mongo_faculty.get('research_info', '')
    
    return {
        'id': mongo_faculty.get('id', ''),
        'Full Name': mongo_faculty.get('name', ''),
        'Email': extract_email_from_text(general_info),
        'Department': extract_department_from_text(general_info),
        'Title': extract_title_from_text(general_info),
        'Office': extract_office_from_text(general_info),
        'Phone': extract_phone_from_text(general_info),
        'Research Interests': research_info.strip(),
        'Bio': general_info.strip()
    }

def admin_format_to_mongo_faculty(admin_faculty):
    """Convert admin dashboard format back to MongoDB format"""
    # Create general_info text from individual fields
    general_info_parts = []
    
    if admin_faculty.get('Full Name'):
        general_info_parts.append(admin_faculty['Full Name'])
    
    if admin_faculty.get('Title'):
        general_info_parts.append(admin_faculty['Title'])
    
    if admin_faculty.get('Department'):
        general_info_parts.append(f"Stevens Institute of Technology, {admin_faculty['Department']}")
    
    if admin_faculty.get('Email'):
        general_info_parts.append(admin_faculty['Email'])
    
    if admin_faculty.get('Phone'):
        general_info_parts.append(admin_faculty['Phone'])
    
    if admin_faculty.get('Office'):
        general_info_parts.append(f"Office: {admin_faculty['Office']}")
    
    if admin_faculty.get('Bio') and admin_faculty['Bio'] != admin_faculty.get('Full Name', ''):
        general_info_parts.append(admin_faculty['Bio'])
    
    return {
        'name': admin_faculty.get('Full Name', ''),
        'general_info': ' | '.join(general_info_parts),
        'research_info': admin_faculty.get('Research Interests', ''),
        'id': admin_faculty.get('id', '')
    }

# Test function
def test_conversion():
    """Test the conversion functions"""
    sample_faculty = {
        "general_info": "Aleksi Aaltonen Academics https://www.stevens.edu/profile/aaaltone  (201) 216-5423 [email protected] Website PhD (2012) The London School of Economics and Political Science (Information Systems) MS (2005) University of Helsinki (Sociology) Before joining academia, I designed and built digital services for organizations such Nokia and CMI – Martti Ahtisaari Peace Foundation founded by Nobel Peace Laureate and former President of Finland Martti Ahtisaari. After completing my PhD at the London School of Economics and Political Science, I cofounded and helped to raise 1.7 million euros funding for an activity tracking app Moves. Apple chose Moves as the Best App of 2013 in the Fitness Revolution category, and the company was acquired by Facebook in April 2014. Associate Professor, Stevens Institute of Technology, NJ, 2024– Assistant Professor, Fox School of Business, Temple University, PA, 2018–2024 Assistant Professor, Warwick Business School, UK, 2014–2018 Deputy Editor-in-Chief, Journal of Information Technology, January 2025– MIS110 Creative Problem Solving in Programming BT416 Business Process Management",
        "id": "6882be05e409dbe8120a6be4",
        "name": "Aleksi Aaltonen",
        "research_info": "Aleksi Aaltonen 0 I study data-based organizing and innovation using various methods. My publications have appeared in Management Science , Information Systems Research , MIS Quarterly , Journal of Management Information Systems and in other high-quality journals. I am also a Deputy Editor-in-Chief at the Journal of Information Technology and I maintain the Data Studies Bibliography that is a scholarly resource for those who approach data as on object of research itself."
    }
    
    print("Original MongoDB format:")
    print(json.dumps(sample_faculty, indent=2))
    
    print("\nConverted to Admin format:")
    admin_format = mongo_faculty_to_admin_format(sample_faculty)
    print(json.dumps(admin_format, indent=2))
    
    print("\nConverted back to MongoDB format:")
    mongo_format = admin_format_to_mongo_faculty(admin_format)
    print(json.dumps(mongo_format, indent=2))

if __name__ == "__main__":
    test_conversion()