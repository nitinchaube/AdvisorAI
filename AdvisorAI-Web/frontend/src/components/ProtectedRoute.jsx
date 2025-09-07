import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import "./LoadingSpinner.css";

const ProtectedRoute = ({
  children,
  requireProfileCompletion = true,
  requireAdmin = false,
  requireEmailVerification = true,
}) => {
  const { currentUser, loading, userProfile, emailVerified } = useAuth();
  const location = useLocation();

  console.log("ProtectedRoute: Current location:", location.pathname);
  console.log("ProtectedRoute: Loading:", loading);
  console.log("ProtectedRoute: Current user:", !!currentUser);
  console.log("ProtectedRoute: User profile:", userProfile);
  console.log("ProtectedRoute: Email verified:", emailVerified);
  console.log(
    "ProtectedRoute: Require profile completion:",
    requireProfileCompletion
  );
  console.log(
    "ProtectedRoute: Require email verification:",
    requireEmailVerification
  );

  // Show a loading spinner while auth state is being determined
  if (loading) {
    console.log("ProtectedRoute: Showing loading spinner (auth loading)");
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading user data...</p>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!currentUser) {
    console.log("ProtectedRoute: No current user, redirecting to login");
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // CRITICAL: Check email verification FIRST, before profile completion
  if (requireEmailVerification && !emailVerified && !currentUser.emailVerified) {
    console.log("ProtectedRoute: Email not verified, redirecting to email verification");
    return <Navigate to="/email-verification" replace state={{ from: location }} />;
  }

  // If authenticated but profile is not yet loaded, show loading spinner
  if (!userProfile) {
    console.log("ProtectedRoute: Showing loading spinner (profile loading)");
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading profile data...</p>
      </div>
    );
  }

  // If profile completion is required, check the userProfile state
  if (requireProfileCompletion) {
    console.log(
      "ProtectedRoute: Profile completion check from userProfile:",
      userProfile.profileCompleted
    );
    if (
      !userProfile.profileCompleted &&
      location.pathname !== "/profile-completion"
    ) {
      console.log(
        "ProtectedRoute: Profile not completed, redirecting to profile-completion"
      );
      return <Navigate to="/profile-completion" replace />;
    }
  }

  // If admin privileges are required, check the userProfile role
  if (requireAdmin && userProfile.role !== "admin") {
    console.log(
      "ProtectedRoute: Admin required, but user is not admin. Redirecting to dashboard."
    );
    return <Navigate to="/dashboard" replace />;
  }

  console.log("ProtectedRoute: All checks passed, rendering protected content");
  // If all checks pass, render the protected content
  return children;
};

export default ProtectedRoute;
