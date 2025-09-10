import json
import os
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

def extract_name(info_string):
   
    #find "Academics" first
    match = re.match(r"^(.*?)\sAcademics", info_string)
    if match:
        return match.group(1).strip()
    
    #if "Academics" not found, try to find a number (for research info)
    match = re.match(r"^(.*?)\s\d+", info_string)
    if match:
        return match.group(1).strip()
    
    return None

def upload_faculty_data_to_mongodb(general_info_path, research_info_path, mongo_uri, db_name, collection_name):
   
    client = None
    try:
        #connect to MongoDB
        client = MongoClient(mongo_uri)
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")

        db = client[db_name]
        collection = db[collection_name]

        #general faculty data
        with open(general_info_path, 'r', encoding='utf-8') as f:
            general_data = json.load(f)

        #research faculty data
        with open(research_info_path, 'r', encoding='utf-8') as f:
            research_data = json.load(f)

        #dictionary to store combined faculty data
        combined_faculty_data = {}

        #general information
        for entry in general_data:
            info_string = entry.get("FacultyGeneralInfo")
            if info_string:
                name = extract_name(info_string)
                if name:
                    if name not in combined_faculty_data:
                        combined_faculty_data[name] = {}
                    combined_faculty_data[name]["general_info"] = info_string
                    
        #research information
        for entry in research_data:
            info_string = entry.get("FacultyResearchInfo")
            if info_string:
                name = extract_name(info_string)
                if name:
                    if name not in combined_faculty_data:
                        combined_faculty_data[name] = {}
                    combined_faculty_data[name]["research_info"] = info_string

        print(f"Starting upload of {len(combined_faculty_data)} faculty records to MongoDB collection '{collection_name}'...")

        #upload combined data to MongoDB
        for name, data in combined_faculty_data.items():
            data["name"] = name #store the full name as a field
            
            try:
                result = collection.update_one(
                    {"name": name},
                    {"$set": data},
                    upsert=True
                )
                if result.upserted_id:
                    print(f"Successfully inserted new faculty: {name}")
                elif result.modified_count > 0:
                    print(f"Successfully updated existing faculty: {name}")
                else:
                    print(f"Faculty {name} already up-to-date.")
            except PyMongoError as e:
                print(f"Error uploading faculty {name}: {e}")

        print("Faculty upload process completed.")

    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
    except FileNotFoundError:
        print(f"Error: One or more JSON files not found. Check paths: {general_info_path}, {research_info_path}.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from one of the files. Please check file formats.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if client:
            client.close()
            print("MongoDB connection closed.")


if __name__ == "__main__":
    MONGO_URI = "mongodb+srv://advisor:EV0nZid23Ns1UDOe@advisorai.wzupxpw.mongodb.net/?retryWrites=true&w=majority&appName=AdvisorAi" 
    DB_NAME = "AdvisorAI"
    COLLECTION_NAME = "faculty"

    general_info_json = 'data/AllFacultyGeneralInformation.json'
    research_info_json = 'data/AllFacultyResearchInformation.json'

    # Call the upload function
    upload_faculty_data_to_mongodb(general_info_json, research_info_json, MONGO_URI, DB_NAME, COLLECTION_NAME)
