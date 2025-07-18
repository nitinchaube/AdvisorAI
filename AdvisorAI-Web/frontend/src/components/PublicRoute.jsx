import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './LoadingSpinner.css';

const PublicRoute = ({ children, redirectTo = "/dashboard" }) => {
  const { currentUser, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking auth state
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If user is authenticated, redirect to specified route
  if (currentUser) {
    // Check if user has completed profile
    const hasCompletedProfile = currentUser.profileCompleted || 
                               localStorage.getItem('profileCompleted') === 'true';
    
    if (!hasCompletedProfile && redirectTo === "/dashboard") {
      return <Navigate to="/profile-completion" replace />;
    }
    
    return <Navigate to={redirectTo} replace />;
  }

  // If not authenticated, show the public page
  return children;
};

export default PublicRoute; 