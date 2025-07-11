import React, { useState } from "react";
import Header from "./Header";
import Footer from "./Footer";
import Sidebar from "./Sidebar";
import ChatInterface from "./ChatInterface";
import ChatHistory from "./ChatHistory";
import RatingPage from "./RatingPage";
import CourseExplorer from "./CourseExplorer";

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistoryOpen, setChatHistoryOpen] = useState(false);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleChatHistoryToggle = () => {
    setChatHistoryOpen(!chatHistoryOpen);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <div className="h-full flex flex-col md:flex-row relative">
            {/* Chat Interface - Takes full width on mobile, left side on desktop */}
            <div className="flex-1 min-w-0 h-full">
              <ChatInterface onToggleHistory={handleChatHistoryToggle} />
            </div>
            
            {/* Chat History - Right sidebar on mobile, always visible on desktop */}
            <div className={`
              ${chatHistoryOpen ? 'block' : 'hidden'} 
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
            `}>
              <ChatHistory onClose={() => setChatHistoryOpen(false)} />
            </div>
          </div>
        );
      case 'history':
        return (
          <div className="h-full w-full">
            <ChatHistory />
          </div>
        );
      case 'ratings':
        return (
          <div className="h-full w-full overflow-hidden">
            <RatingPage />
          </div>
        );
      case 'courses':
        return (
          <div className="h-full w-full overflow-hidden">
            <CourseExplorer />
          </div>
        );
      case 'analytics':
        return (
          <div className="h-full w-full bg-gradient-to-br from-violet-50 via-purple-50 to-indigo-50 overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent mb-4">Analytics Dashboard</h1>
                <p className="text-lg text-gray-700">Track your academic progress and insights</p>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 p-8">
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-r from-violet-500 via-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                    <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
                  <p className="text-gray-600">We're building amazing analytics features for you!</p>
                </div>
              </div>
            </div>
          </div>
        );
      case 'schedule':
        return (
          <div className="h-full w-full bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent mb-4">Schedule Planner</h1>
                <p className="text-lg text-gray-700">Plan your academic calendar efficiently</p>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 p-8">
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                    <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
                  <p className="text-gray-600">Smart scheduling features are on the way!</p>
                </div>
              </div>
            </div>
          </div>
        );
      case 'documents':
        return (
          <div className="h-full w-full bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 overflow-y-auto">
            <div className="max-w-4xl mx-auto p-8">
              <div className="text-center mb-12">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent mb-4">Document Manager</h1>
                <p className="text-lg text-gray-700">Organize and manage your academic files</p>
              </div>
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 p-8">
                <div className="text-center py-12">
                  <div className="w-24 h-24 bg-gradient-to-r from-orange-500 via-amber-500 to-yellow-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                    <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-2">Coming Soon</h3>
                  <p className="text-gray-600">Document management features coming soon!</p>
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
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 relative overflow-hidden">
      {/* Enhanced Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/40 via-indigo-900/30 to-blue-900/40"></div>
      
      {/* Animated gradient orbs */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-rose-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-gradient-to-br from-blue-500/20 via-cyan-500/20 to-teal-500/20 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-violet-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '4s'}}></div>
      
      {/* Subtle grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
      
      {/* Fixed Header */}
      <div className="flex-shrink-0 z-50 relative">
        <Header 
          onMenuToggle={handleMenuToggle}
          sidebarOpen={sidebarOpen}
        />
      </div>

      {/* Main Content Area - Between Header and Footer */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Sidebar - Between header and footer */}
        {sidebarOpen && (
          <div className="flex-shrink-0 z-40 relative">
            <Sidebar 
              activeTab={activeTab} 
              setActiveTab={setActiveTab}
            />
          </div>
        )}

        {/* Content - Takes remaining space */}
        <div className="flex-1 relative overflow-hidden">
          {renderContent()}
        </div>
      </div>

      {/* Fixed Footer */}
      <div className="flex-shrink-0 z-50 relative">
        <Footer />
      </div>
    </div>
  );
};

export default Dashboard; 