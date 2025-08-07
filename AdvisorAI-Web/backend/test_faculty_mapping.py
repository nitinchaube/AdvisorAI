#!/usr/bin/env python3
"""
Test faculty data mapping with real data
"""

from faculty_data_mapper import mongo_faculty_to_admin_format, admin_format_to_mongo_faculty
import json

# Your actual faculty data
sample_faculty = {
    "general_info": "Aleksi Aaltonen Academics https://www.stevens.edu/profile/aaaltone  (201) 216-5423 [email protected] Website PhD (2012) The London School of Economics and Political Science (Information Systems) MS (2005) University of Helsinki (Sociology) Before joining academia, I designed and built digital services for organizations such Nokia and CMI – Martti Ahtisaari Peace Foundation founded by Nobel Peace Laureate and former President of Finland Martti Ahtisaari. After completing my PhD at the London School of Economics and Political Science, I cofounded and helped to raise 1.7 million euros funding for an activity tracking app Moves. Apple chose Moves as the Best App of 2013 in the Fitness Revolution category, and the company was acquired by Facebook in April 2014. Associate Professor, Stevens Institute of Technology, NJ, 2024– Assistant Professor, Fox School of Business, Temple University, PA, 2018–2024 Assistant Professor, Warwick Business School, UK, 2014–2018 Deputy Editor-in-Chief, Journal of Information Technology, January 2025– MIS110 Creative Problem Solving in Programming BT416 Business Process Management",
    "id": "6882be05e409dbe8120a6be4",
    "name": "Aleksi Aaltonen",
    "research_info": "Aleksi Aaltonen 0 I study data-based organizing and innovation using various methods. My publications have appeared in Management Science , Information Systems Research , MIS Quarterly , Journal of Management Information Systems and in other high-quality journals. I am also a Deputy Editor-in-Chief at the Journal of Information Technology and I maintain the Data Studies Bibliography that is a scholarly resource for those who approach data as on object of research itself.  "
}

print("🧪 Testing Faculty Data Mapping")
print("=" * 50)

print("\n1. Original MongoDB Format:")
print(json.dumps(sample_faculty, indent=2))

print("\n2. Converted to Admin Dashboard Format:")
admin_format = mongo_faculty_to_admin_format(sample_faculty)
print(json.dumps(admin_format, indent=2))

print("\n3. Key Extracted Fields:")
print(f"✅ Full Name: '{admin_format['Full Name']}'")
print(f"✅ Email: '{admin_format['Email']}'")
print(f"✅ Phone: '{admin_format['Phone']}'")
print(f"✅ Title: '{admin_format['Title']}'")
print(f"✅ Department: '{admin_format['Department']}'")
print(f"✅ Research Interests: '{admin_format['Research Interests'][:100]}...'")

print("\n4. What the Admin Dashboard Will Show:")
print("Instead of 'N/A', you'll now see:")
print(f"  Name: {admin_format['Full Name']}")
print(f"  Email: {admin_format['Email']}")
print(f"  Department: {admin_format['Department']}")
print(f"  Title: {admin_format['Title']}")
print(f"  Office: {admin_format['Office'] or 'Not specified'}")

print("\n✅ The faculty data should now display correctly in the admin dashboard!")
print("📝 Note: When you edit faculty, the system will convert back to MongoDB format.")