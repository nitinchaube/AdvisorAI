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
import ChatPage from "./components/ChatPage.jsx";
import ChatHistoryPage from "./components/ChatHistoryPage.jsx";
import RatingsPageComponent from "./components/RatingsPage.jsx";
import CourseExplorerPage from "./components/CourseExplorerPage.jsx";
import AnalyticsPage from "./components/AnalyticsPage.jsx";
import SchedulePage from "./components/SchedulePage.jsx";
import DocumentsPage from "./components/DocumentsPage.jsx";
import ProfileCompletion from "./components/ProfileCompletion.jsx";
import ProfileData from "./components/ProfileData.jsx";
import CourseDetails from "./components/CourseDetails";
import AdminDashboard from "./components/AdminDashboard";
import PortfolioView from "./components/PortfolioView";
import JobSearchPage from "./components/JobSearchPage.jsx";
import InternshipSearchPage from "./components/InternshipSearchPage.jsx";
import PlannerPage from "./components/PlannerPage.jsx";

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
              <PublicRoute redirectTo="/chat">
                <Signup />
              </PublicRoute>
            }
          />
          <Route
            path="/login"
            element={
              <PublicRoute redirectTo="/chat">
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

          {/* Main Dashboard Routes */}
          <Route
            path="/chat"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat-history"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <ChatHistoryPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ratings"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <RatingsPageComponent />
              </ProtectedRoute>
            }
          />
          <Route
            path="/course-explorer"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <CourseExplorerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/professor/:professorId"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <CourseExplorerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/course/:courseId"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <CourseExplorerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/planner"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <PlannerPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/documents"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <DocumentsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/job-search"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <JobSearchPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/internship-search"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <InternshipSearchPage />
              </ProtectedRoute>
            }
          />

          {/* Legacy Dashboard Route - Redirect to chat */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute requireProfileCompletion={true}>
                <ChatPage />
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

          {/* Public Portfolio Route */}
          <Route path="/portfolio/:portfolioName" element={<PortfolioView />} />

          {/* Catch all route - redirect to chat */}
          <Route
            path="*"
            element={
              <PublicRoute redirectTo="/chat">
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
