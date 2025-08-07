#!/usr/bin/env python3
"""
Script to create or promote a user to admin role in AdvisorAI
This script works with Firebase UIDs and MongoDB
"""

import os
from pymongo import MongoClient
from datetime import datetime
import sys
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI')
if not MONGO_URI:
    print("❌ Error: MONGO_URI environment variable not set")
    print("Please check your .env file")
    sys.exit(1)

try:
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client['AdvisorAI']
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    sys.exit(1)

def list_users():
    """List all users in the database"""
    try:
        users = list(mongo_db.users.find({}, {
            "uid": 1, 
            "email": 1, 
            "fullName": 1, 
            "role": 1, 
            "_id": 0
        }))
        if users:
            print("\n📋 Current users:")
            print("-" * 80)
            for i, user in enumerate(users, 1):
                role = user.get('role', 'user')
                name = user.get('fullName', 'N/A')
                email = user.get('email', 'N/A')
                uid = user.get('uid', 'N/A')
                role_emoji = "👑" if role == 'admin' else "👤"
                print(f"{i}. {role_emoji} {email}")
                print(f"   Name: {name}")
                print(f"   UID: {uid}")
                print(f"   Role: {role}")
                print("-" * 40)
        else:
            print("\n📋 No users found in database")
        return users
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return []

def promote_user_to_admin_by_email(email):
    """Promote an existing user to admin role by email"""
    try:
        # Check if user exists
        user = mongo_db.users.find_one({"email": email})
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
        
        # Update user role
        result = mongo_db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "role": "admin",
                    "updatedAt": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully promoted {email} to admin role")
            print(f"🔑 User UID: {user.get('uid', 'N/A')}")
            return True
        else:
            current_role = user.get('role', 'user')
            if current_role == 'admin':
                print(f"⚠️  User {email} is already an admin")
            else:
                print(f"⚠️  No changes made to user {email}")
            return True
            
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        return False

def promote_user_to_admin_by_uid(uid):
    """Promote an existing user to admin role by Firebase UID"""
    try:
        # Check if user exists
        user = mongo_db.users.find_one({"uid": uid})
        if not user:
            print(f"❌ User with UID '{uid}' not found")
            return False
        
        # Update user role
        result = mongo_db.users.update_one(
            {"uid": uid},
            {
                "$set": {
                    "role": "admin",
                    "updatedAt": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            email = user.get('email', 'N/A')
            print(f"✅ Successfully promoted user to admin role")
            print(f"📧 Email: {email}")
            print(f"🔑 UID: {uid}")
            return True
        else:
            current_role = user.get('role', 'user')
            if current_role == 'admin':
                print(f"⚠️  User is already an admin")
            else:
                print(f"⚠️  No changes made to user")
            return True
            
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        return False

def check_admin_access():
    """Check if there are any admin users"""
    try:
        admin_count = mongo_db.users.count_documents({"role": "admin"})
        print(f"\n👑 Current admin users: {admin_count}")
        
        if admin_count == 0:
            print("⚠️  WARNING: No admin users found!")
            print("   You should create at least one admin user to access the admin dashboard.")
        else:
            admins = list(mongo_db.users.find(
                {"role": "admin"}, 
                {"email": 1, "fullName": 1, "uid": 1, "_id": 0}
            ))
            print("\n👑 Admin users:")
            for admin in admins:
                name = admin.get('fullName', 'N/A')
                email = admin.get('email', 'N/A')
                print(f"   • {email} ({name})")
                
    except Exception as e:
        print(f"❌ Error checking admin access: {e}")

def main():
    """Main function"""
    print("🔧 AdvisorAI Admin User Management Tool")
    print("=" * 50)
    
    # Check current admin status
    check_admin_access()
    
    while True:
        print("\nOptions:")
        print("1. List all users")
        print("2. Promote user to admin (by email)")
        print("3. Promote user to admin (by Firebase UID)")
        print("4. Check admin users")
        print("5. Show setup instructions")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            list_users()
            
        elif choice == "2":
            users = list_users()
            if not users:
                print("No users found to promote")
                continue
                
            email = input("\nEnter email address to promote to admin: ").strip().lower()
            if email:
                promote_user_to_admin_by_email(email)
            else:
                print("❌ Email cannot be empty")
                
        elif choice == "3":
            users = list_users()
            if not users:
                print("No users found to promote")
                continue
                
            uid = input("\nEnter Firebase UID to promote to admin: ").strip()
            if uid:
                promote_user_to_admin_by_uid(uid)
            else:
                print("❌ UID cannot be empty")
                
        elif choice == "4":
            check_admin_access()
            
        elif choice == "5":
            print("\n📋 Setup Instructions:")
            print("=" * 30)
            print("1. Create a regular user account through the frontend:")
            print("   • Go to your React app (http://localhost:3000)")
            print("   • Click 'Sign Up' and create an account")
            print("   • Complete the profile setup")
            print("")
            print("2. Run this script to promote the user to admin:")
            print("   • Use option 2 (by email) - easier")
            print("   • Or use option 3 (by UID) - more precise")
            print("")
            print("3. Login to see the admin dashboard:")
            print("   • Login with your credentials")
            print("   • Look for 'Admin Portal' link in the header")
            print("   • Click it to access /admin")
            print("")
            print("🔧 Troubleshooting:")
            print("• If you don't see 'Admin Portal' link:")
            print("  - Check MongoDB: role field should be 'admin'")
            print("  - Clear browser cache and reload")
            print("  - Check browser console for errors")
            print("")
            
        elif choice == "6":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-6")

if __name__ == "__main__":
    main()