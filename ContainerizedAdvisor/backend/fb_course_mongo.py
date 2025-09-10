import json
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

def upload_course_data_to_mongodb(json_file_path, mongo_uri, db_name, collection_name):
    
    client = None

    try:
        client = MongoClient(mongo_uri)
        
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")

        db = client[db_name]
        collection = db[collection_name]

    
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("Error: JSON data is not a list of objects. Expected a list of courses.")
            return

        print(f"Starting upload of {len(data)} courses to MongoDB collection '{collection_name}'...")
        
        #upload each course as a document
        for i, course in enumerate(data):
            course_code = course.get("Course Code")
            if not course_code:
                print(f"Skipping course at index {i} due to missing 'Course Code'.")
                continue

            try:
                result = collection.update_one(
                    {"Course Code": course_code},
                    {"$set": course},
                    upsert=True
                )
                if result.upserted_id:
                    print(f"Successfully inserted new course: {course_code}")
                elif result.modified_count > 0:
                    print(f"Successfully updated existing course: {course_code}")
                else:
                    print(f"Course {course_code} already up-to-date.")
            except PyMongoError as e:
                print(f"Error uploading course {course_code}: {e}")

        print("Course upload process completed.")

    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_file_path}. Please check file format.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if client:
            client.close()
            print("MongoDB connection closed.")


if __name__ == "__main__":
    MONGO_URI = "mongodb+srv://advisor:EV0nZid23Ns1UDOe@advisorai.wzupxpw.mongodb.net/?retryWrites=true&w=majority&appName=AdvisorAi" 
    DB_NAME = "AdvisorAI"
    COLLECTION_NAME = "courses"

    json_file = 'data/AllCourseRelatedData.json'

    # Call the upload function
    upload_course_data_to_mongodb(json_file, MONGO_URI, DB_NAME, COLLECTION_NAME)
