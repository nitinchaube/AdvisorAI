import React, { useEffect, useState } from "react";
import Header from "./Header";
import Footer from "./Footer";
import Sidebar from "./Sidebar";

const PageLayout = ({ children, sidebarOpen, onMenuToggle }) => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

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
        <Header onMenuToggle={onMenuToggle} sidebarOpen={sidebarOpen} />
      </div>

      {/* Main Content Area - Between Header and Footer */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Mobile: Sidebar as overlay with backdrop */}
        {isMobile && sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-30 backdrop-blur-sm"
            onClick={onMenuToggle}
          />
        )}

        {/* Sidebar - overlay on mobile, inline on desktop */}
        {sidebarOpen && (
          <div
            className={
              isMobile
                ? "fixed top-0 left-0 h-full z-40 shadow-2xl pt-16"
                : "flex-shrink-0 z-40 relative"
            }
          >
            <Sidebar />
          </div>
        )}

        {/* Content - Takes remaining space */}
        <div className="flex-1 relative overflow-hidden">
          {children}
        </div>
      </div>

      {/* Fixed Footer */}
      <div className="flex-shrink-0 z-50 relative">
        <Footer />
      </div>
    </div>
  );
};

export default PageLayout;
