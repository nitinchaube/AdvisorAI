import React, { useState } from "react";
import PageLayout from "./PageLayout";

const SchedulePage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
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
    </PageLayout>
  );
};

export default SchedulePage;
