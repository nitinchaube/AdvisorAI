# Profile Management & Authentication Flow

## Overview
This document outlines the complete profile management flow and authentication behavior in the AdvisorAI application.

## Authentication Flow

### 1. New User Registration
```
1. User visits /signup
2. Fills registration form
3. Firebase account created
4. Backend JWT token obtained
5. Profile completion status set to 'false'
6. Redirected to /profile-completion
```

### 2. User Login
```
1. User visits /login
2. Fills login form
3. Firebase authentication
4. Backend JWT token obtained
5. Check profile completion status:
   - Profile completed → /dashboard
   - Profile not completed → /profile-completion
```

### 3. Profile Completion (First Time)
```
1. User uploads resume
2. AI extracts information
3. User reviews/edits data
4. Profile saved to backend
5. Profile completion marked as 'true'
6. Redirected to /dashboard
```

### 4. Profile Editing (Subsequent Visits)
```
1. User clicks "Edit Profile" from dashboard
2. Navigate to /profile-completion
3. Existing profile data loaded automatically
4. User can edit information or upload new resume
5. Changes saved to backend
6. Stay on profile page with success message
```

## Route Protection Rules

### Public Routes (Redirect Authenticated Users)
- **`/`** → Redirects to `/dashboard` if authenticated
- **`/login`** → Redirects to `/dashboard` if authenticated  
- **`/signup`** → Redirects to `/dashboard` if authenticated

### Protected Routes
- **`/profile-completion`** → Requires authentication, no profile completion required
- **`/dashboard`** → Requires authentication + profile completion

## Profile Completion Page Behavior

### First Time Users (No Profile)
```
1. Show upload view by default
2. User uploads resume
3. AI processes and extracts data
4. Show form with extracted data
5. User can edit before saving
6. Save marks profile as completed
7. Redirect to dashboard
```

### Returning Users (Profile Exists)
```
1. Show loading spinner while fetching profile
2. Load existing profile data from backend
3. Show form view directly with existing data
4. User can edit information
5. Save updates profile (no redirect)
6. Show success message
```

## Dashboard Integration

### Profile Management Section
Located in the Analytics tab of the dashboard:

```
┌─────────────────────────────────────────────────────────┐
│ Profile Management Links                                │
├─────────────────────────────────────────────────────────┤
│ Profile Data                    [View Profile Data]     │
│ View and edit all your profile information              │
├─────────────────────────────────────────────────────────┤
│ Edit Profile                     [Edit Profile]         │
│ Update your resume and profile information              │
└─────────────────────────────────────────────────────────┘
```

### Links Available
- **View Profile Data**: Links to `/profile-data` (existing functionality)
- **Edit Profile**: Links to `/profile-completion` (new functionality)

## State Management

### Profile Completion Status
- **Storage**: `localStorage.getItem('profileCompleted')`
- **Values**: `'true'` | `'false'` | `null`
- **Default**: `'false'` for new users, `null` for logged out users

### Profile Data
- **Storage**: Backend database
- **Loading**: Fetched via API when editing existing profile
- **Caching**: Form data stored in component state during editing

## User Experience Features

### 1. Smart Loading States
- **New users**: Upload view with resume processing
- **Returning users**: Loading spinner while fetching profile
- **Processing**: Progress indicators during AI extraction

### 2. Contextual UI
- **First time**: "Upload Your Resume" with AI extraction
- **Editing**: "Update Your Resume" with existing data loaded
- **Buttons**: "Save Profile" vs "Update Profile"

### 3. Success Feedback
- **First save**: Success message + redirect to dashboard
- **Updates**: Success message + stay on page
- **Loading**: Clear loading indicators

### 4. Error Handling
- **Upload failures**: Specific error messages
- **API errors**: Graceful fallbacks
- **Network issues**: Retry mechanisms

## Technical Implementation

### ProfileCompletion Component States
```javascript
const [currentView, setCurrentView] = useState(0); // 0: Upload, 1: Form
const [loadingExistingProfile, setLoadingExistingProfile] = useState(false);
const [parsing, setParsing] = useState(false);
const [formData, setFormData] = useState({});
```

### Conditional Rendering Logic
```javascript
// Loading existing profile
if (loadingExistingProfile) {
  return <LoadingSpinner />
}

// Show upload or form based on current view
if (currentView === 0) {
  return <UploadView />
} else {
  return <FormView />
}
```

### Save vs Update Logic
```javascript
const handleSave = isProfileCompleted() ? handleUpdateProfile : handleSaveProfile;
```

## Security & Validation

### Authentication Guards
- **Client-side**: Route protection components
- **Server-side**: JWT token validation
- **Profile access**: User-specific data isolation

### Data Validation
- **File uploads**: Type and size validation
- **Form data**: Required field validation
- **API responses**: Error handling and fallbacks

## Best Practices Implemented

### 1. User Experience
- ✅ No infinite redirect loops
- ✅ Clear loading states
- ✅ Contextual UI based on user state
- ✅ Smooth transitions between states

### 2. Data Management
- ✅ Automatic profile loading for returning users
- ✅ Form state preservation during editing
- ✅ Optimistic updates with error handling
- ✅ Clean state management

### 3. Security
- ✅ Authentication required for profile access
- ✅ User-specific data isolation
- ✅ Secure token management
- ✅ Input validation and sanitization

### 4. Performance
- ✅ Lazy loading of profile data
- ✅ Efficient state updates
- ✅ Minimal API calls
- ✅ Responsive UI updates

## Testing Scenarios

### 1. New User Flow
```
1. Register new account
2. Verify redirect to profile completion
3. Upload resume and verify AI extraction
4. Save profile and verify dashboard redirect
5. Verify profile completion status is 'true'
```

### 2. Returning User Flow
```
1. Login with existing account
2. Verify direct redirect to dashboard
3. Click "Edit Profile" from dashboard
4. Verify existing profile data loads
5. Make changes and save
6. Verify success message and no redirect
```

### 3. Authentication Flow
```
1. Try to access dashboard without login → redirect to login
2. Try to access login while authenticated → redirect to dashboard
3. Try to access profile completion without login → redirect to login
4. Verify profile completion enforcement works
```

This implementation provides a seamless, secure, and user-friendly profile management experience that follows industry best practices. 