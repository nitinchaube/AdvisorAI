import { useState } from "react";
import reactLogo from "./assets/react.svg";
import { Route, Routes, NavLink } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import PublicRoute from "./components/PublicRoute.jsx";
import Signup from "./components/Signup.jsx";
import Home from "./components/Home.jsx";
import Login from "./components/Login.jsx";
import Dashboard from "./components/Dashboard.jsx";
import ProfileCompletion from "./components/ProfileCompletion.jsx";
import ProfileData from "./components/ProfileData.jsx";
import CourseDetails from "./components/CourseDetails";
import AdminDashboard from "./components/AdminDashboard";

function App() {
  return (
    <AuthProvider>
      <div>
        <Routes>
          {/* Public Routes - Redirect authenticated users */}
          <Route path="/" element={<Home />} />
          <Route
            path="/signup"
            element={
              <PublicRoute redirectTo="/dashboard">
                <Signup />
              </PublicRoute>
            }
          />
          <Route
            path="/login"
            element={
              <PublicRoute redirectTo="/dashboard">
                <Login />
              </PublicRoute>
            }
          />

          {/* Protected Routes - Require authentication */}
          <Route
            path="/profile-completion"
            element={
              <ProtectedRoute requireProfileCompletion={false}>
                <ProfileCompletion />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile-data"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <ProfileData />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin={true}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          {/* Catch all route - redirect to home */}
          <Route
            path="*"
            element={
              <PublicRoute redirectTo="/dashboard">
                <Home />
              </PublicRoute>
            }
          />
        </Routes>
      </div>
    </AuthProvider>
  );
}

export default App;
