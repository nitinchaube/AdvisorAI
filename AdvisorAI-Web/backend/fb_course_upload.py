import firebase_admin
from firebase_admin import firestore
import json
import os

def upload_data_to_firebase(json_file_path):
    """Upload course data to Firestore using Application Default Credentials."""
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()

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
        print(f"Error: Required file not found. Check path: {json_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}. Please check file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    # Course data JSON file
    json_file = 'data/AllCourseRelatedData.json'

    # Uses ADC — run `gcloud auth application-default login` first for local dev
    upload_data_to_firebase(json_file)
