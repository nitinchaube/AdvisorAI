import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import "./LoadingSpinner.css";

const PublicRoute = ({ children, redirectTo = "/dashboard" }) => {
  const { currentUser, loading, userProfile } = useAuth();
  const location = useLocation();

  // Show a loading spinner while auth state or user profile is being determined
  if (loading || (currentUser && !userProfile)) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // If user is authenticated, handle redirection
  if (currentUser) {
    // If profile is not complete and the intended redirect is to the dashboard,
    // force the user to the profile completion page.
    if (userProfile && !userProfile.profileCompleted) {
      return <Navigate to="/profile-completion" replace />;
    }

    // Otherwise, redirect to the intended page (e.g., dashboard)
    return <Navigate to={redirectTo} replace />;
  }

  // If not authenticated, render the public page (e.g., login, signup)
  return children;
};

export default PublicRoute;
