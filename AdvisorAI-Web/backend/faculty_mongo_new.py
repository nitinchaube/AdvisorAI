import json
import re
from pymongo import MongoClient
import pandas as pd

def parse_education(education_string):
    """
    Parses the education string into a list of structured education objects.
    """
    if not education_string or pd.isna(education_string):
        return []

    # Regex to capture degree, year, institution, and field
    # This regex is designed to be flexible for various formats
    education_entries = []
    # Split by common degree prefixes
    parts = re.split(r'(PhD|Ph\.D\.|MS|M\.S\.|MBA|M\.B\.A\.|BS|B\.S\.|BE|B\.E\.|JD|J\.D\.|DMA|BBA|Other degree|Other)', education_string)

    # The first element might be empty if the string starts with a degree
    if not parts[0].strip():
        parts = parts[1:]

    i = 0
    while i < len(parts):
        degree_info = {}
        degree_info['degree'] = parts[i].strip()
        
        if i + 1 < len(parts):
            details = parts[i+1]
            
            # Extract year
            year_match = re.search(r'\((\d{4})\)', details)
            if year_match:
                degree_info['year'] = year_match.group(1)
                details = details.replace(year_match.group(0), '').strip()
            else:
                degree_info['year'] = None

            # The remaining part is institution and field
            field_match = re.search(r'\((.*?)\)', details)
            if field_match:
                degree_info['field'] = field_match.group(1).strip()
                degree_info['institution'] = details.replace(field_match.group(0), '').strip()
            else:
                degree_info['institution'] = details.strip()
                degree_info['field'] = None
            
            education_entries.append(degree_info)

        i += 2
        
    return education_entries


def process_data(file_path):
    """
    Reads a JSON file, transforms it into a structured format, and returns a list of faculty documents.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return []
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []

    df = pd.DataFrame(data)
    faculty_list = []

    for index, row in df.iterrows():
        faculty_member = {
            "name": row.get("Name"),
            "title": row.get("Title"),
            "profileURL": row.get("Profile URL"),
            "address": row.get("Address"),
            "phone": row.get("Phone"),
            "email": row.get("Email"),
            "website": row.get("Website"),
            "education": parse_education(row.get("Education")),
            "research": row.get("Research"),
            "institutionalService": [{"role": item.split(' ', 1)[0], "committee": item.split(' ', 1)[1]} for item in (row.get("Institutional Service", "") or "").split('\n') if item.strip()],
            "professionalService": [{"role": item.split(' ', 1)[0], "organization": item.split(' ', 1)[1]} for item in (row.get("Professional Service", "") or "").split('\n') if item.strip()],
            "appointments": [{"title": item.split(',', 1)[0], "organization": item.split(',', 1)[1].strip() if ',' in item else item, "duration": ""} for item in (row.get("Appointments", "") or "").split('\n') if item.strip()],
            "professionalSocieties": [{"society": item.split(' ', 1)[0], "role": item.split(' ', 1)[1]} for item in (row.get("Professional Societies", "") or "").split('\n') if item.strip()],
            "publications": {
                "books": [{"title": item.split('(')[0].strip(), "year": re.search(r'\((\d{4})\)', item).group(1) if re.search(r'\((\d{4})\)', item) else None, "publisher": item.split('). ')[1] if '). ' in item else ""} for item in (row.get("Selected Publications - Book", "") or "").split('\n') if item.strip()],
                "bookChapters": [{"title": item.split('.')[0].strip(), "bookTitle": "", "year": re.search(r'\((\d{4})\)', item).group(1) if re.search(r'\((\d{4})\)', item) else None, "publisher": ""} for item in (row.get("Selected Publications - Book Chapter", "") or "").split('\n') if item.strip()],
                "journalArticles": [{"title": item.split('.')[0].strip(), "journal": "", "year": re.search(r'\((\d{4})\)', item).group(1) if re.search(r'\((\d{4})\)', item) else None, "volume": "", "issue": "", "pages": ""} for item in (row.get("Selected Publications - Journal Article", "") or "").split('\n') if item.strip()],
                "conferenceProceedings": [{"title": item.split('.')[0].strip(), "conference": "", "year": re.search(r'\((\d{4})\)', item).group(1) if re.search(r'\((\d{4})\)', item) else None} for item in (row.get("Selected Publications - Conference Proceeding", "") or "").split('\n') if item.strip()],
            },
            "generalInformation": row.get("General Information"),
            "honorsAndAwards": [{"award": item.split(',')[0].strip(), "year": item.split(',')[-1].strip()} for item in (row.get("Honors and Awards", "") or "").split('\n') if item.strip()],
            "grantsAndContracts": [{"title": item.split(',')[0].strip(), "agency": "", "amount": "", "period": "", "role": ""} for item in (row.get("Grants, Contracts and Funds", "") or "").split('\n') if item.strip()],
            "courses": [course.strip() for course in (row.get("Courses", "") or "").split('\n') if course.strip()],
            "experience": [{"title": item.split(',')[0].strip(), "organization": "", "duration": ""} for item in (row.get("Experience", "") or "").split('\n') if item.strip()]
        }
        faculty_list.append(faculty_member)
        
    return faculty_list

def upload_to_mongodb(data, connection_string, db_name, collection_name):
    """
    Uploads a list of documents to a MongoDB collection.
    """
    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]
    
    # Clear existing data in the collection to avoid duplicates on re-runs
    collection.delete_many({})
    
    # Insert new data
    if data:
        collection.insert_many(data)
        print(f"Successfully uploaded {len(data)} documents to the '{collection_name}' collection in the '{db_name}' database.")
    else:
        print("No data to upload.")

if __name__ == "__main__":
    # --- Configuration ---
    MONGO_CONNECTION_STRING = "mongodb+srv://advisor:EV0nZid23Ns1UDOe@advisorai.wzupxpw.mongodb.net/?retryWrites=true&w=majority&appName=AdvisorAi"
    DB_NAME = "AdvisorAI"
    COLLECTION_NAME = "faculty_new"
    
    files_to_process = [
        "data/faculty_data/faculty_directory1.json",
        "data/faculty_data/faculty_directory1-2.json",
        "data/faculty_data/faculty_directory1-3.json"
    ]
    
    all_faculty_data = []
    for file in files_to_process:
        print(f"Processing {file}...")
        all_faculty_data.extend(process_data(file))
        
    if all_faculty_data:
        upload_to_mongodb(all_faculty_data, MONGO_CONNECTION_STRING, DB_NAME, COLLECTION_NAME)

