#!/usr/bin/env python3
"""
Test script for Admin Dashboard functionality
Tests both courses and faculty admin CRUD operations
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5002/api"
ADMIN_TOKEN = None  # Will be set after login

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

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

def test_admin_auth():
    """Test admin authentication"""
    print_section("Testing Admin Authentication")
    
    # Try to access admin endpoint without token
    response = make_request("GET", "/admin/courses")
    print_test("Access admin endpoint without token", 
               response and response.status_code == 401,
               f"Status: {response.status_code if response else 'No response'}")
    
    return response is not None

def test_courses_crud():
    """Test courses CRUD operations"""
    print_section("Testing Courses CRUD Operations")
    
    if not ADMIN_TOKEN:
        print("❌ Skipping courses tests - no admin token")
        return False
    
    # Test data
    test_course = {
        "Course Code": "TEST 101",
        "Course Title": "Test Course for Admin Dashboard",
        "Course Description": "This is a test course created by the admin dashboard test script",
        "Credits": "3",
        "Department": "Test Department",
        "Level": "Undergraduate",
        "Prerequisites": "None"
    }
    
    course_id = None
    
    # Test: Get all courses
    response = make_request("GET", "/admin/courses", token=ADMIN_TOKEN)
    print_test("Get all courses", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    # Test: Add new course
    response = make_request("POST", "/admin/courses", data=test_course, token=ADMIN_TOKEN)
    success = response and response.status_code == 201
    if success:
        data = response.json()
        course_id = data.get('id')
    print_test("Add new course", success,
               f"Course ID: {course_id}" if course_id else "Failed to get course ID")
    
    if not course_id:
        print("❌ Skipping remaining course tests - failed to create course")
        return False
    
    # Test: Get specific course
    response = make_request("GET", f"/admin/courses/{course_id}", token=ADMIN_TOKEN)
    print_test("Get specific course", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    # Test: Update course
    updated_course = test_course.copy()
    updated_course["Course Title"] = "Updated Test Course"
    updated_course["Credits"] = "4"
    
    response = make_request("PUT", f"/admin/courses/{course_id}", data=updated_course, token=ADMIN_TOKEN)
    print_test("Update course", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    # Test: Delete course
    response = make_request("DELETE", f"/admin/courses/{course_id}", token=ADMIN_TOKEN)
    print_test("Delete course", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    return True

def test_faculty_crud():
    """Test faculty CRUD operations"""
    print_section("Testing Faculty CRUD Operations")
    
    if not ADMIN_TOKEN:
        print("❌ Skipping faculty tests - no admin token")
        return False
    
    # Test data
    test_faculty = {
        "Full Name": "Dr. Test Professor",
        "Email": "test.professor@test.edu",
        "Department": "Test Department",
        "Title": "Test Professor",
        "Office": "Test Building 123",
        "Phone": "(555) 123-4567",
        "Research Interests": "Testing, Quality Assurance, Software Engineering",
        "Bio": "Dr. Test Professor is a fictional professor created for testing the admin dashboard."
    }
    
    faculty_id = None
    
    # Test: Get all faculty
    response = make_request("GET", "/admin/faculty", token=ADMIN_TOKEN)
    print_test("Get all faculty", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    # Test: Add new faculty
    response = make_request("POST", "/admin/faculty", data=test_faculty, token=ADMIN_TOKEN)
    success = response and response.status_code == 201
    if success:
        data = response.json()
        faculty_id = data.get('id')
    print_test("Add new faculty", success,
               f"Faculty ID: {faculty_id}" if faculty_id else "Failed to get faculty ID")
    
    if not faculty_id:
        print("❌ Skipping remaining faculty tests - failed to create faculty")
        return False
    
    # Test: Get specific faculty
    response = make_request("GET", f"/admin/faculty/{faculty_id}", token=ADMIN_TOKEN)
    print_test("Get specific faculty", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    # Test: Update faculty
    updated_faculty = test_faculty.copy()
    updated_faculty["Full Name"] = "Dr. Updated Test Professor"
    updated_faculty["Title"] = "Senior Test Professor"
    
    response = make_request("PUT", f"/admin/faculty/{faculty_id}", data=updated_faculty, token=ADMIN_TOKEN)
    print_test("Update faculty", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    # Test: Delete faculty
    response = make_request("DELETE", f"/admin/faculty/{faculty_id}", token=ADMIN_TOKEN)
    print_test("Delete faculty", 
               response and response.status_code == 200,
               f"Status: {response.status_code if response else 'No response'}")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Admin Dashboard Test Suite")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test authentication
    auth_ok = test_admin_auth()
    
    if not auth_ok:
        print("\n❌ Authentication tests failed. Cannot proceed with CRUD tests.")
        print("\n💡 To run CRUD tests:")
        print("1. Start the backend server")
        print("2. Create an admin user in MongoDB")
        print("3. Login through the frontend to get a valid admin token")
        print("4. Set ADMIN_TOKEN variable in this script")
        return
    
    # Note: CRUD tests require a valid admin token
    print("\n💡 To test CRUD operations:")
    print("1. Login as an admin user through the frontend")
    print("2. Get the JWT token from localStorage")
    print("3. Set ADMIN_TOKEN variable in this script")
    print("4. Re-run this script")
    
    if ADMIN_TOKEN:
        # Test courses CRUD
        courses_ok = test_courses_crud()
        
        # Test faculty CRUD
        faculty_ok = test_faculty_crud()
        
        # Summary
        print_section("Test Summary")
        print(f"Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
        print(f"Courses CRUD: {'✅ PASS' if courses_ok else '❌ FAIL'}")
        print(f"Faculty CRUD: {'✅ PASS' if faculty_ok else '❌ FAIL'}")
    else:
        print_section("Test Summary")
        print(f"Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
        print("Courses CRUD: ⏭️ SKIPPED (No admin token)")
        print("Faculty CRUD: ⏭️ SKIPPED (No admin token)")

if __name__ == "__main__":
    main()