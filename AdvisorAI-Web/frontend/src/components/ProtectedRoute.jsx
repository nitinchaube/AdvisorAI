import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './LoadingSpinner.css';

const ProtectedRoute = ({ children, requireProfileCompletion = true, requireAdmin = false }) => {
  const { currentUser, loading, userProfile, isProfileCompleted } = useAuth();
  const location = useLocation();

  console.log('ProtectedRoute: Current location:', location.pathname);
  console.log('ProtectedRoute: Loading:', loading);
  console.log('ProtectedRoute: Current user:', currentUser);
  console.log('ProtectedRoute: Require profile completion:', requireProfileCompletion);

  // Show loading spinner while checking auth state
  if (loading) {
    console.log('ProtectedRoute: Showing loading spinner');
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!currentUser) {
    console.log('ProtectedRoute: No current user, redirecting to login');
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // If profile completion is required and user hasn't completed profile
  if (requireProfileCompletion) {
    const hasCompletedProfile = isProfileCompleted();
    console.log('ProtectedRoute: Profile completion check (using isProfileCompleted):', hasCompletedProfile);
    if (!hasCompletedProfile && location.pathname !== '/profile-completion') {
      console.log('ProtectedRoute: Profile not completed, redirecting to profile-completion');
      return <Navigate to="/profile-completion" replace />;
    }
  }

  // After profile check
  if (requireAdmin && userProfile?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  console.log('ProtectedRoute: All checks passed, showing protected content');
  // If all checks pass, show the protected content
  return children;
};

export default ProtectedRoute; 