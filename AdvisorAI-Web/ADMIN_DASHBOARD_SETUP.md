# Admin Dashboard Setup Guide

This guide explains how to set up and use the Admin Dashboard for managing Courses and Professors in the AdvisorAI application.

## Features

The Admin Dashboard provides a complete CRUD (Create, Read, Update, Delete) interface for:

### Courses Management

- View all courses in a sortable, searchable table
- Add new courses with fields like:
  - Course Code (e.g., CS 513)
  - Course Title
  - Course Description
  - Credits
  - Department
  - Level (Undergraduate/Graduate/PhD)
  - Prerequisites
- Edit existing courses
- Delete courses (with confirmation)

### Faculty Management

- View all faculty members in a sortable, searchable table
- Add new faculty with fields like:
  - Full Name
  - Email
  - Department
  - Title
  - Office
  - Phone
  - Research Interests
  - Bio
- Edit existing faculty
- Delete faculty (also removes related reviews)

## Setup Instructions

### 1. Backend Setup

The backend already includes the necessary admin endpoints:

#### Course Admin Endpoints

- `GET /api/admin/courses` - Get all courses
- `POST /api/admin/courses` - Add new course
- `GET /api/admin/courses/<id>` - Get specific course
- `PUT /api/admin/courses/<id>` - Update course
- `DELETE /api/admin/courses/<id>` - Delete course

#### Faculty Admin Endpoints

- `GET /api/admin/faculty` - Get all faculty
- `POST /api/admin/faculty` - Add new faculty
- `GET /api/admin/faculty/<id>` - Get specific faculty
- `PUT /api/admin/faculty/<id>` - Update faculty
- `DELETE /api/admin/faculty/<id>` - Delete faculty

### 2. Admin User Setup

To access the admin dashboard, you need a user with admin role:

1. Create a user account through the regular signup process
2. In MongoDB, update the user document to include admin role:

```javascript
// In MongoDB shell or Compass
db.users.updateOne({ email: "admin@example.com" }, { $set: { role: "admin" } });
```

### 3. Frontend Access

Once you have an admin user:

1. Login with your admin credentials
2. You'll see an "Admin Portal" link in the header menu
3. Click it to access `/admin` route
4. The admin dashboard will load with tabs for Courses and Faculty

## Usage Guide

### Navigation

- **Courses Tab**: Manage course catalog
- **Faculty Tab**: Manage faculty directory
- **Search**: Real-time search across relevant fields
- **Add Button**: Opens modal for creating new items

### Adding Items

1. Click "Add Course" or "Add Faculty" button
2. Fill in the required fields in the modal
3. Click "Add" to save

### Editing Items

1. Click the edit icon (pencil) next to any item
2. Modify fields in the modal
3. Click "Update" to save changes

### Deleting Items

1. Click the delete icon (trash) next to any item
2. Confirm deletion in the popup
3. Item will be permanently removed

### Search and Filter

- Use the search box to filter items by name, code, department, etc.
- Search is case-insensitive and matches partial text

## Security

- All admin endpoints require JWT authentication
- Admin role is verified on every request
- Non-admin users are redirected to dashboard
- All operations are logged for audit purposes

## API Integration

The admin dashboard integrates with the existing Chroma vector database:

- Course additions/updates sync to Chroma for chatbot search
- Course deletions remove data from Chroma
- Faculty changes update the knowledge base

## Testing

Run the test script to verify admin functionality:

```bash
cd AdvisorAI-Web/backend
python test_admin_dashboard.py
```

Note: To test CRUD operations, you'll need to set a valid admin JWT token in the script.

## Troubleshooting

### Common Issues

1. **"Admin access required" error**

   - Solution: Ensure user has `role: "admin"` in MongoDB

2. **"Failed to fetch" errors**

   - Solution: Check backend server is running on port 5002
   - Verify JWT token is valid

3. **Empty tables**

   - Solution: Check MongoDB collections have data
   - Verify API endpoints are responding

4. **Navigation not showing admin link**
   - Solution: Ensure user profile includes admin role
   - Check AuthContext is loading user profile correctly

### Debug Steps

1. Check browser console for JavaScript errors
2. Verify network requests in DevTools
3. Check backend logs for API errors
4. Confirm MongoDB connection and data

## Architecture

### Frontend Components

- `AdminDashboard.jsx` - Main dashboard component
- `ProtectedRoute.jsx` - Admin authentication wrapper
- `AuthContext.jsx` - User role management

### Backend Components

- `app.py` - Admin API endpoints
- MongoDB collections: `courses`, `faculty`
- JWT authentication with role-based access

### Data Flow

1. User authenticates and gets JWT token
2. Frontend checks user role via AuthContext
3. Admin routes protected by ProtectedRoute component
4. API calls include JWT token for authorization
5. Backend verifies admin role before processing
6. MongoDB operations executed with audit logging

## Future Enhancements

Potential improvements for the admin dashboard:

1. **Bulk Operations**

   - Import/export CSV files
   - Bulk edit multiple items
   - Batch delete with selection

2. **Advanced Search**

   - Filter by multiple criteria
   - Date range filters
   - Advanced query builder

3. **Analytics**

   - Usage statistics
   - Popular courses/professors
   - User activity logs

4. **Audit Trail**

   - Change history tracking
   - User action logs
   - Rollback capabilities

5. **Media Management**
   - Course image uploads
   - Faculty photo management
   - Document attachments
