import firebase_admin
from firebase_admin import firestore
import json
import os
import re

def extract_name(info_string):
   
    #find "Academics" first
    match = re.match(r"^(.*?)\sAcademics", info_string)
    if match:
        return match.group(1).strip()
    
    #if "Academics" not found, try to find a number
    match = re.match(r"^(.*?)\s\d+", info_string)
    if match:
        return match.group(1).strip()
    
    return None

def upload_faculty_data_to_firebase(general_info_path, research_info_path):
    """Upload faculty data to Firestore using Application Default Credentials."""
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()

        db = firestore.client()

        #general faculty data
        with open(general_info_path, 'r', encoding='utf-8') as f:
            general_data = json.load(f)

        #research faculty data
        with open(research_info_path, 'r', encoding='utf-8') as f:
            research_data = json.load(f)

        #dictionary to store combined faculty data
        combined_faculty_data = {}

        #process general information
        for entry in general_data:
            info_string = entry.get("FacultyGeneralInfo")
            if info_string:
                name = extract_name(info_string)
                if name:
                    if name not in combined_faculty_data:
                        combined_faculty_data[name] = {}
                    combined_faculty_data[name]["general_info"] = info_string
                    
        #process research information
        for entry in research_data:
            info_string = entry.get("FacultyResearchInfo")
            if info_string:
                name = extract_name(info_string)
                if name:
                    if name not in combined_faculty_data:
                        combined_faculty_data[name] = {}
                    combined_faculty_data[name]["research_info"] = info_string


        print(f"Starting upload of {len(combined_faculty_data)} faculty records to Firestore...")

        #combined data and upload to Firestore
        for name, data in combined_faculty_data.items():
            #sanitize name for use as a document ID
            doc_id = re.sub(r'[^\w\s-]', '', name).replace(' ', '_').lower()
            
            try:
                doc_ref = db.collection('faculty').document(doc_id)
                doc_ref.set(data)
                print(f"Successfully uploaded faculty: {name} (ID: {doc_id})")
            except Exception as e:
                print(f"Error uploading faculty {name} (ID: {doc_id}): {e}")

        print("Upload process completed.")

    except FileNotFoundError:
        print(f"Error: One or more JSON files not found. Check paths: {general_info_path}, {research_info_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from one of the files. Please check file formats.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Paths to your faculty data JSON files
    general_info_json = 'data/AllFacultyGeneralInformation.json'
    research_info_json = 'data/AllFacultyResearchInformation.json'

    # Uses ADC — run `gcloud auth application-default login` first for local dev
    upload_faculty_data_to_firebase(general_info_json, research_info_json)
