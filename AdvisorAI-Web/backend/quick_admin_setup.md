# Quick Admin User Setup

## Method 1: Using the Python Script (Recommended)

```bash
cd AdvisorAI-Web/backend
python create_admin_user.py
```

Then:

1. Choose option 1 to list users
2. Choose option 2 to promote by email (easiest)
3. Enter the email address of the user you want to make admin

## Method 2: Direct MongoDB Commands

### Option A: Using MongoDB Compass

1. Connect to your MongoDB database
2. Navigate to the `AdvisorAI` database
3. Open the `users` collection
4. Find your user document
5. Add or update the `role` field to `"admin"`

### Option B: Using MongoDB Shell

```javascript
// Connect to your MongoDB
use AdvisorAI

// List all users to find the one you want to promote
db.users.find({}, {email: 1, fullName: 1, uid: 1, role: 1})

// Promote user by email
db.users.updateOne(
  { email: "your-email@example.com" },
  {
    $set: {
      role: "admin",
      updatedAt: new Date()
    }
  }
)

// OR promote user by Firebase UID (more precise)
db.users.updateOne(
  { uid: "firebase-uid-here" },
  {
    $set: {
      role: "admin",
      updatedAt: new Date()
    }
  }
)

// Verify the update
db.users.findOne({ email: "your-email@example.com" }, { role: 1, email: 1 })
```

## Method 3: Quick Copy-Paste Commands

Replace `YOUR_EMAIL_HERE` with your actual email:

```javascript
// For MongoDB Compass or Shell
db.users.updateOne({ email: "YOUR_EMAIL_HERE" }, { $set: { role: "admin" } });
```

## Verification Steps

1. **Check in MongoDB:**

   ```javascript
   db.users.findOne({ email: "your-email@example.com" }, { role: 1, email: 1 });
   ```

   Should return: `{ role: "admin", email: "your-email@example.com" }`

2. **Check in Frontend:**
   - Login to your React app
   - Look for "Admin Portal" link in the header menu
   - Click it to access `/admin`
   - You should see the admin dashboard

## Troubleshooting

### "Admin Portal" link not showing:

1. **Check user role in MongoDB:**

   ```javascript
   db.users.findOne({ email: "your-email@example.com" });
   ```

2. **Clear browser cache and reload**

3. **Check browser console for errors**

4. **Make sure you're logged in with the correct account**

### Admin dashboard shows "Admin access required":

1. **Check the JWT token contains correct user ID**
2. **Verify the `uid` field matches between Firebase and MongoDB**
3. **Check backend logs for detailed error messages**

### User not found in database:

1. **Make sure you've signed up through the frontend first**
2. **Complete the profile setup process**
3. **Check if the user exists in MongoDB:**
   ```javascript
   db.users.find({ email: "your-email@example.com" });
   ```

## Important Notes

- ⚠️ **The user MUST sign up through the frontend first** to create their Firebase authentication
- 🔑 **The system uses Firebase UID as the primary identifier**, not email
- 👑 **Only users with `role: "admin"` can access admin features**
- 🔒 **Admin role is checked on every API request** for security

## Step-by-Step Process

1. **Create Regular Account:**

   - Go to your React app (http://localhost:3000)
   - Sign up with email/password
   - Complete profile setup

2. **Promote to Admin:**

   - Run the Python script: `python create_admin_user.py`
   - Or use MongoDB command directly

3. **Access Admin Dashboard:**
   - Login to the app
   - Click "Admin Portal" in header
   - Start managing courses and faculty!
