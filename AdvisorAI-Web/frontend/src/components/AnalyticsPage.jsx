import React, { useState } from "react";
import PageLayout from "./PageLayout";
import { Link } from "react-router-dom";

const AnalyticsPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
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
    </PageLayout>
  );
};

export default AnalyticsPage;
