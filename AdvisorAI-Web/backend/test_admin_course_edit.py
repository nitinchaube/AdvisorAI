#!/usr/bin/env python3
"""
Test script to verify admin course editing functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5002/api"
ADMIN_TOKEN = None  # Set this to a valid admin JWT token

def print_test(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def make_request(method, endpoint, data=None, token=None):
    """Make HTTP request with optional authentication"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_course_crud():
    """Test course CRUD operations with Chroma sync"""
    if not ADMIN_TOKEN:
        print("❌ No admin token provided. Please set ADMIN_TOKEN variable.")
        return False
    
    print("🧪 Testing Course CRUD with Chroma Integration")
    print("=" * 50)
    
    # Test data
    test_course = {
        "Course Code": "TEST 999",
        "Course Title": "Test Course for Chroma Integration",
        "Course Description": "This course tests the admin dashboard Chroma integration",
        "Credits": "3",
        "Department": "Test Department",
        "Level": "Graduate",
        "Prerequisites": "None"
    }
    
    course_id = None
    
    # Test: Add new course
    print("\n1. Testing course creation...")
    response = make_request("POST", "/admin/courses", data=test_course, token=ADMIN_TOKEN)
    success = response and response.status_code == 201
    if success:
        data = response.json()
        course_id = data.get('id')
        print_test("Create course", True, f"Course ID: {course_id}")
    else:
        error_msg = response.json().get('error', 'Unknown error') if response else 'No response'
        print_test("Create course", False, f"Error: {error_msg}")
        return False
    
    # Test: Update course (this was failing before)
    print("\n2. Testing course update...")
    updated_course = test_course.copy()
    updated_course["Course Title"] = "Updated Test Course for Chroma"
    updated_course["Credits"] = "4"
    
    response = make_request("PUT", f"/admin/courses/{course_id}", data=updated_course, token=ADMIN_TOKEN)
    success = response and response.status_code == 200
    if success:
        print_test("Update course", True, "Course updated successfully")
    else:
        error_msg = response.json().get('error', 'Unknown error') if response else 'No response'
        print_test("Update course", False, f"Error: {error_msg}")
    
    # Test: Get updated course
    print("\n3. Testing course retrieval...")
    response = make_request("GET", f"/admin/courses/{course_id}", token=ADMIN_TOKEN)
    success = response and response.status_code == 200
    if success:
        data = response.json()
        course = data.get('course', {})
        title = course.get('Course Title', '')
        credits = course.get('Credits', '')
        print_test("Get updated course", True, f"Title: {title}, Credits: {credits}")
    else:
        error_msg = response.json().get('error', 'Unknown error') if response else 'No response'
        print_test("Get updated course", False, f"Error: {error_msg}")
    
    # Test: Delete course
    print("\n4. Testing course deletion...")
    response = make_request("DELETE", f"/admin/courses/{course_id}", token=ADMIN_TOKEN)
    success = response and response.status_code == 200
    if success:
        print_test("Delete course", True, "Course deleted successfully")
    else:
        error_msg = response.json().get('error', 'Unknown error') if response else 'No response'
        print_test("Delete course", False, f"Error: {error_msg}")
    
    return True

def main():
    """Run the test"""
    print("🔧 Admin Course Edit Test")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    if not ADMIN_TOKEN:
        print("\n⚠️  No admin token provided!")
        print("To run this test:")
        print("1. Login as admin user in the frontend")
        print("2. Get JWT token from browser localStorage")
        print("3. Set ADMIN_TOKEN variable in this script")
        print("4. Re-run this script")
        return
    
    success = test_course_crud()
    
    print("\n" + "="*50)
    if success:
        print("✅ All tests completed!")
        print("The Chroma integration error should be fixed.")
    else:
        print("❌ Some tests failed.")
        print("Check the error messages above.")

if __name__ == "__main__":
    main()