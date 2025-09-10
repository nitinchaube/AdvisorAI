# Authentication & Routing Rules Documentation

## Overview
This document outlines the professional authentication guards and page redirection rules implemented in the AdvisorAI application.

## Route Types

### 1. Public Routes (PublicRoute Component)
**Purpose**: Routes that should redirect authenticated users away from them.

**Routes**:
- `/` (Home)
- `/login`
- `/signup`

**Behavior**:
- ✅ **Unauthenticated users**: Can access normally
- ❌ **Authenticated users**: Automatically redirected to `/dashboard`
- 🔄 **Loading state**: Shows spinner while checking auth status

**Implementation**:
```jsx
<PublicRoute redirectTo="/dashboard">
  <Component />
</PublicRoute>
```

### 2. Protected Routes (ProtectedRoute Component)
**Purpose**: Routes that require authentication and optionally profile completion.

**Routes**:
- `/profile-completion` (requires auth, no profile completion required)
- `/dashboard` (requires auth + profile completion)

**Behavior**:
- ❌ **Unauthenticated users**: Redirected to `/login`
- ⚠️ **Authenticated users without profile**: Redirected to `/profile-completion`
- ✅ **Authenticated users with profile**: Can access normally
- 🔄 **Loading state**: Shows spinner while checking auth status

**Implementation**:
```jsx
// Profile completion (no profile required)
<ProtectedRoute requireProfileCompletion={false}>
  <ProfileCompletion />
</ProtectedRoute>

// Dashboard (profile completion required)
<ProtectedRoute requireProfileCompletion={true}>
  <Dashboard />
</ProtectedRoute>
```

## Authentication Flow

### 1. User Registration (Signup)
```
1. User fills signup form
2. Firebase account created
3. Backend JWT token obtained
4. Profile completion status set to 'false'
5. Redirect to /profile-completion
```

### 2. User Login
```
1. User fills login form
2. Firebase authentication
3. Backend JWT token obtained
4. Check profile completion status
5. Redirect based on status:
   - Profile completed → /dashboard
   - Profile not completed → /profile-completion
```

### 3. Profile Completion
```
1. User uploads resume
2. AI extracts information
3. User reviews/edits data
4. Profile saved to backend
5. Profile completion marked as 'true'
6. Redirect to /dashboard
```

### 4. Logout
```
1. Clear localStorage (backendToken, profileCompleted)
2. Firebase signout
3. Redirect to / (home)
```

## State Management

### Profile Completion Status
- **Storage**: `localStorage.getItem('profileCompleted')`
- **Values**: `'true'` | `'false'` | `null`
- **Default**: `'false'` for new users, `null` for logged out users

### Authentication Tokens
- **Firebase**: Handled automatically by Firebase Auth
- **Backend**: `localStorage.getItem('backendToken')`

## Route Guards Logic

### PublicRoute Logic
```javascript
if (loading) {
  return <LoadingSpinner />
}

if (currentUser) {
  if (!hasCompletedProfile && redirectTo === "/dashboard") {
    return <Navigate to="/profile-completion" />
  }
  return <Navigate to={redirectTo} />
}

return children // Show public page
```

### ProtectedRoute Logic
```javascript
if (loading) {
  return <LoadingSpinner />
}

if (!currentUser) {
  return <Navigate to="/login" state={{ from: location }} />
}

if (requireProfileCompletion && !hasCompletedProfile) {
  return <Navigate to="/profile-completion" />
}

return children // Show protected page
```

## Error Handling

### Authentication Errors
- **Invalid credentials**: Show specific error messages
- **Network errors**: Graceful fallback with retry options
- **Token expiration**: Automatic redirect to login

### Route Protection Errors
- **Unauthorized access**: Redirect to appropriate page
- **Missing profile**: Force profile completion flow
- **Loading timeouts**: Show user-friendly loading states

## Security Features

### 1. Token Management
- Backend JWT tokens stored in localStorage
- Automatic token refresh handling
- Secure token transmission in API calls

### 2. Route Protection
- Client-side route guards prevent unauthorized access
- Server-side validation for all protected endpoints
- Automatic redirects based on user state

### 3. Profile Completion Enforcement
- Users cannot access dashboard without completing profile
- Profile completion status persisted across sessions
- Clear separation between authenticated and profile-completed states

## User Experience Features

### 1. Loading States
- Consistent loading spinners during auth checks
- Smooth transitions between route changes
- User-friendly loading messages

### 2. Redirect Handling
- Preserve intended destination after login
- Smart redirects based on user state
- No infinite redirect loops

### 3. Error Recovery
- Clear error messages for authentication failures
- Automatic retry mechanisms
- Graceful degradation for network issues

## Best Practices Implemented

### 1. Professional Authentication Flow
- ✅ Proper route guards for all pages
- ✅ Loading states during auth checks
- ✅ Smart redirects based on user state
- ✅ Profile completion enforcement
- ✅ Secure token management

### 2. User Experience
- ✅ No infinite redirect loops
- ✅ Clear loading indicators
- ✅ Intuitive navigation flow
- ✅ Error handling and recovery

### 3. Security
- ✅ Client-side route protection
- ✅ Server-side validation
- ✅ Secure token storage
- ✅ Automatic logout on errors

### 4. Code Quality
- ✅ Reusable route guard components
- ✅ Centralized auth state management
- ✅ Clean separation of concerns
- ✅ Comprehensive error handling

## Usage Examples

### Adding a New Public Route
```jsx
<Route 
  path="/about" 
  element={
    <PublicRoute redirectTo="/dashboard">
      <AboutPage />
    </PublicRoute>
  } 
/>
```

### Adding a New Protected Route
```jsx
<Route 
  path="/settings" 
  element={
    <ProtectedRoute requireProfileCompletion={true}>
      <SettingsPage />
    </ProtectedRoute>
  } 
/>
```

### Custom Redirect Logic
```jsx
<PublicRoute redirectTo="/custom-page">
  <CustomComponent />
</PublicRoute>
```

This implementation follows industry best practices for authentication and routing in React applications, providing a secure and user-friendly experience. 