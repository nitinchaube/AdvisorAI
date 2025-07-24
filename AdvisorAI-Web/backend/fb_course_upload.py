import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

def upload_data_to_firebase(json_file_path, firebase_config_path):
   
    try:
        if not os.path.exists(firebase_config_path):
            print(f"Error: Firebase credentials file not found at {firebase_config_path}")
            return

        cred = credentials.Certificate(firebase_config_path)
        firebase_admin.initialize_app(cred)

        db = firestore.client()

        #load data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("Error: JSON data is not a list of objects. Expected a list of courses.")
            return

        print(f"Starting upload of {len(data)} courses to Firestore...")
        
        #upload each course as a document
        for i, course in enumerate(data):
            course_code = course.get("Course Code")
            if not course_code:
                print(f"Skipping course at index {i} due to missing 'Course Code'.")
                continue

            try:
                #course_code as document ID for easy retrieval and uniqueness
                doc_ref = db.collection('courses').document(course_code)
                doc_ref.set(course)
                print(f"Successfully uploaded course: {course_code}")
            except Exception as e:
                print(f"Error uploading course {course_code}: {e}")

        print("Upload process completed.")

    except FileNotFoundError:
        print(f"Error: Required file not found. Check paths: {json_file_path} or {firebase_config_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path} or {firebase_config_path}. Please check file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    firebase_credentials_file = 'firebase_key.json'

    #course data JSON file
    json_file = 'data/AllCourseRelatedData.json'

  
    upload_data_to_firebase(json_file, firebase_credentials_file)
