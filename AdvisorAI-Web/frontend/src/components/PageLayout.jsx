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
    <div className="h-screen flex flex-col relative overflow-hidden" style={{ background: `linear-gradient(to bottom right, var(--theme-page-bg-from), var(--theme-page-bg-via), var(--theme-page-bg-to))` }}>
      {/* Background overlay */}
      <div className="absolute inset-0" style={{ background: `linear-gradient(to bottom right, var(--theme-orb-1), var(--theme-orb-2), var(--theme-orb-3))` }}></div>

      {/* Animated gradient orbs */}
      <div className="absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl animate-pulse" style={{ background: `linear-gradient(to bottom right, var(--theme-orb-1), var(--theme-orb-2))` }}></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 rounded-full blur-3xl animate-pulse" style={{ animationDelay: "2s", background: `linear-gradient(to bottom right, var(--theme-orb-2), var(--theme-orb-3))` }}></div>
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full blur-3xl animate-pulse" style={{ animationDelay: "4s", background: `linear-gradient(to bottom right, var(--theme-orb-3), var(--theme-orb-1))` }}></div>

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
