import React, { useState } from "react";
import PageLayout from "./PageLayout";

const DocumentsPage = () => {
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
    </PageLayout>
  );
};

export default DocumentsPage;
