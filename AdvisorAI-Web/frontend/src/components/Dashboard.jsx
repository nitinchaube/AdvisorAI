import React, { useState, useEffect } from "react";
import Header from "./Header";
import Footer from "./Footer";
import Sidebar from "./Sidebar";
import ChatInterface from "./ChatInterface";
import ChatSessionManager from "./ChatSessionManager";
import ChatHistoryView from "./ChatHistoryView";
import RatingPage from "./RatingPage";
import CourseExplorer from "./CourseExplorer";
import CourseDetails from "./CourseDetails";
import ProfessorDetails from "./ProfessorDetails";

import { Link } from "react-router-dom";
import { apiService } from "../services/api";
import { chatCache } from "../utils/chatCache";

const Dashboard = () => {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentSessionTitle, setCurrentSessionTitle] = useState("New Chat");
  const [chatHistoryOpen, setChatHistoryOpen] = useState(false);
  // Sidebar hidden on mobile by default, open on desktop
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);
  const [activeTab, setActiveTab] = useState("chat");
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [selectedProfessorId, setSelectedProfessorId] = useState(null);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleChatHistoryToggle = () => {
    setChatHistoryOpen(!chatHistoryOpen);
  };

  const handleNewChat = async (sessionId) => {
    if (sessionId) {
      setCurrentSessionId(sessionId);
      await loadSessionTitle(sessionId);
    } else {
      // Create a new chat session only when user explicitly requests it
      try {
        const response = await apiService.createChatSession("New Chat");
        if (response.success) {
          setCurrentSessionId(response.session_id);
          setCurrentSessionTitle("New Chat");
          localStorage.setItem("currentChatSessionId", response.session_id);
          // Don't clear cache for new sessions - let the messages persist
          console.log("📱 Created new chat session:", response.session_id);
        }
      } catch (error) {
        console.error("Error creating new chat session:", error);
      }
    }
    setChatHistoryOpen(false);
  };

  const handleSessionSelect = (sessionId) => {
    setCurrentSessionId(sessionId);
    localStorage.setItem("currentChatSessionId", sessionId); // <-- Add this line
    loadSessionTitle(sessionId);
    setChatHistoryOpen(false);
  };

  const handleSessionUpdate = (sessionId, newTitle) => {
    if (sessionId === currentSessionId) {
      setCurrentSessionTitle(newTitle);
    }
  };

  const handleSelect = (itemId, category) => {
    if (category === "course") {
      setSelectedCourseId(itemId);
      setSelectedProfessorId(null); // Clear the other ID
    } else if (category === "professor") {
      setSelectedProfessorId(itemId);
      setSelectedCourseId(null);
    }
  };

  const loadSessionTitle = async (sessionId) => {
    try {
      const response = await apiService.getChatSessionMessages(sessionId);
      if (response.success) {
        setCurrentSessionTitle(response.session.title);
      }
    } catch (error) {
      console.error("Error loading session title:", error);
    }
  };

  // Initialize session only once on component mount
  useEffect(() => {
    const initializeSession = async () => {
      if (sessionInitialized) return;

      try {
        // Check if we have a stored session ID
        const storedSessionId = localStorage.getItem("currentChatSessionId");

        if (storedSessionId) {
          // Try to load the stored session
          try {
            const response = await apiService.getChatSessionMessages(
              storedSessionId
            );
            if (response.success) {
              setCurrentSessionId(storedSessionId);
              setCurrentSessionTitle(response.session.title);
              console.log(
                "📱 Restored previous chat session:",
                storedSessionId
              );
              setSessionInitialized(true);
              return;
            } else {
              // Session not found, remove from localStorage
              localStorage.removeItem("currentChatSessionId");
            }
          } catch (error) {
            // Session not found or error, remove from localStorage
            localStorage.removeItem("currentChatSessionId");
            console.log(
              "Could not restore previous session, removed from localStorage"
            );
          }
        }

        // Don't create a new session automatically - let user choose when to start chatting
        setSessionInitialized(true);
        console.log(
          "No session restored, waiting for user to start chatting"
        );
      } catch (error) {
        console.error("Error initializing session:", error);
        setSessionInitialized(true);
      }
    };

    if (activeTab === "chat") {
      initializeSession();
    }
  }, [activeTab, sessionInitialized]);

  const renderContent = () => {
    switch (activeTab) {
      case "chat":
        return (
          <div className="h-full flex flex-col md:flex-row relative">
            {/* Chat Interface - Takes full width on mobile, left side on desktop */}
            <div className="flex-1 min-w-0 h-full">
              <ChatInterface
                onToggleHistory={handleChatHistoryToggle}
                currentSessionId={currentSessionId}
                onSessionUpdate={handleSessionUpdate}
                sessionTitle={currentSessionTitle}
                onNewChat={() => handleNewChat(null)}
              />
            </div>

            {/* Chat Session Manager - Right sidebar on mobile, always visible on desktop */}
            <div
              className={`
              ${chatHistoryOpen ? "block" : "hidden"} 
              md:block 
              absolute md:relative 
              top-0 right-0 
              w-full md:w-80 
              h-full 
              z-30 
              border-l border-white/20 
              backdrop-blur-sm 
              bg-white/10 
              flex-shrink-0
              md:bg-gradient-to-br md:from-slate-900/95 md:via-purple-900/90 md:to-indigo-900/95
            `}
            >
              <ChatSessionManager
                onSessionSelect={handleSessionSelect}
                onNewChat={handleNewChat}
                onClose={() => setChatHistoryOpen(false)}
                currentSessionId={currentSessionId}
                onSessionUpdate={handleSessionUpdate}
              />
            </div>
          </div>
        );
      case "history":
        return (
          <div className="h-full w-full">
            <ChatHistoryView
              currentSessionId={currentSessionId}
              onSessionSelect={handleSessionSelect}
              onNewChat={handleNewChat}
              onSessionUpdate={handleSessionUpdate}
            />
          </div>
        );
      case "ratings":
        return (
          <div className="h-full w-full overflow-hidden">
            <RatingPage />
          </div>
        );
      case "courses":
        if (selectedProfessorId) {
          // Check for professor first
          return (
            <ProfessorDetails
              professorId={selectedProfessorId}
              onBack={() => setSelectedProfessorId(null)}
            />
          );
        }
        if (selectedCourseId) {
          return (
            <CourseDetails
              courseId={selectedCourseId}
              onBack={() => setSelectedCourseId(null)}
            />
          );
        }
        return (
          <div className="h-full w-full overflow-hidden">
            {/* Pass the new handler to CourseExplorer */}
            <CourseExplorer onSelectCourse={handleSelect} />
          </div>
        );
      case "analytics":
        return (
          <div className="h-full w-full bg-white overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
                  Analytics Dashboard
                </h1>
                <p className="text-lg text-slate-700">
                  Track your academic progress and insights
                </p>
              </div>

              {/* Profile Management Links */}
              <div className="bg-white rounded-3xl shadow-lg border border-slate-200/60 p-6 mb-8">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Profile Data Link */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-slate-900 mb-2">
                        Profile Data
                      </h3>
                      <p className="text-slate-600">
                        View and edit all your profile information from the
                        database
                      </p>
                    </div>
                    <Link
                      to="/profile-data"
                      className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg border border-blue-300/30"
                    >
                      View Profile Data
                    </Link>
                  </div>

                  {/* Edit Profile Link */}
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-slate-900 mb-2">
                        Edit Profile
                      </h3>
                      <p className="text-slate-600">
                        Update your resume and profile information
                      </p>
                    </div>
                    <Link
                      to="/profile-completion"
                      className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg border border-blue-300/30"
                    >
                      Edit Profile
                    </Link>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-3xl shadow-lg border border-slate-200/60 p-8">
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-md border border-blue-300/30">
                    <svg
                      className="w-12 h-12 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-slate-900 mb-2">
                    Coming Soon
                  </h3>
                  <p className="text-slate-600">
                    We're building amazing analytics features for you!
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      case "planner":
        return (
          <div className="h-full w-full bg-white overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
                  Schedule Planner
                </h1>
                <p className="text-lg text-slate-700">
                  Plan your academic calendar efficiently
                </p>
              </div>
              <div className="bg-white rounded-3xl shadow-lg border border-slate-200/60 p-8">
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-md border border-blue-300/30">
                    <svg
                      className="w-12 h-12 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-slate-900 mb-2">
                    Coming Soon
                  </h3>
                  <p className="text-slate-600">
                    Smart scheduling features are on the way!
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      case "documents":
        return (
          <div className="h-full w-full bg-white overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
                  Document Manager
                </h1>
                <p className="text-lg text-slate-700">
                  Organize and manage your academic files
                </p>
              </div>
              <div className="bg-white rounded-3xl shadow-lg border border-slate-200/60 p-8">
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-r from-blue-500 via-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-md border border-blue-300/30">
                    <svg
                      className="w-12 h-12 text-white"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-slate-900 mb-2">
                    Coming Soon
                  </h3>
                  <p className="text-slate-600">
                    Document management features coming soon!
                  </p>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return <ChatInterface />;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 relative overflow-hidden">
      {/* Enhanced Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-100/30 via-purple-100/20 to-indigo-100/30"></div>

      {/* Animated gradient orbs */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-blue-200/20 via-purple-200/20 to-indigo-200/20 rounded-full blur-3xl animate-pulse"></div>
      <div
        className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-br from-indigo-200/20 via-blue-200/20 to-cyan-200/20 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: "2s" }}
      ></div>
      <div
        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-purple-200/15 via-blue-200/15 to-indigo-200/15 rounded-full blur-3xl animate-pulse"
        style={{ animationDelay: "4s" }}
      ></div>

      {/* Subtle grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]"></div>

      {/* Fixed Header */}
      <div className="flex-shrink-0 z-50 relative">
        <Header onMenuToggle={handleMenuToggle} sidebarOpen={sidebarOpen} />
      </div>

      {/* Main Content Area - Between Header and Footer */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Mobile sidebar overlay backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/30 z-30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar - fixed overlay on mobile, static on desktop */}
        {sidebarOpen && (
          <div className="fixed md:relative top-0 left-0 h-full z-40 flex-shrink-0 pt-[65px] md:pt-0">
            <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
          </div>
        )}

        {/* Content - Takes remaining space */}
        <div className="flex-1 relative overflow-hidden w-full">{renderContent()}</div>
      </div>

      {/* Fixed Footer */}
      <div className="flex-shrink-0 z-50 relative">
        <Footer />
      </div>
    </div>
  );
};

export default Dashboard;
