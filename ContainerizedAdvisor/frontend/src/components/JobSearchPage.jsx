import React, { useState, useEffect, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Header from "./Header";
import Footer from "./Footer";
import Sidebar from "./Sidebar";
import JobCard from "./JobCard";
import FilterPanel from "./FilterPanel";
import Pagination from "./Pagination";
import { apiService } from "../services/api";
import "./JobSearch.css";
import {
  Briefcase,
  Search,
  Loader,
  AlertCircle,
  Grid,
  List,
  SlidersHorizontal,
} from "lucide-react";

const JobSearchPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Extract type from URL path
  const isInternshipPage = location.pathname.includes("internship");
  const pageType = isInternshipPage ? "internship" : "job";

  // State management
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({});
  const [viewMode, setViewMode] = useState("grid"); // 'grid' or 'list'
  const [showFilters, setShowFilters] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true); // Sidebar toggle state

  // Filter and pagination state
  const [filters, setFilters] = useState({
    search: "",
    workModel: "all",
    location: "",
    companySize: "all",
    industry: "",
    ...(isInternshipPage ? { hireTime: "" } : { h1bSponsored: "all" }),
  });

  const [pagination, setPagination] = useState({
    current_page: 1,
    per_page: 20,
    total_items: 0,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });

  // Debounced search
  const [searchDebounceTimer, setSearchDebounceTimer] = useState(null);

  // Handle sidebar toggle
  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Fetch jobs with filters and pagination
  const fetchJobs = useCallback(
    async (page = 1, currentFilters = filters) => {
      setLoading(true);
      setError(null);

      try {
        const endpoint = isInternshipPage ? "/internships" : "/jobs";
        const params = new URLSearchParams({
          page: page.toString(),
          per_page: pagination.per_page.toString(),
          ...currentFilters,
        });

        const response = await apiService.get(`${endpoint}?${params}`);

        if (response.success) {
          setJobs(response[isInternshipPage ? "internships" : "jobs"] || []);
          setPagination(response.pagination || {});
        } else {
          throw new Error(response.error || "Failed to fetch data");
        }
      } catch (err) {
        setError(err.message || "Failed to load job listings");
        setJobs([]);
      } finally {
        setLoading(false);
      }
    },
    [filters, pagination.per_page, isInternshipPage]
  );

  // Fetch statistics
  const fetchStats = useCallback(async () => {
    try {
      const endpoint = isInternshipPage ? "/internships/stats" : "/jobs/stats";
      const response = await apiService.get(endpoint);

      if (response.success) {
        setStats(response.stats || {});
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  }, [isInternshipPage]);

  // Handle filter changes with debouncing for search
  const handleFiltersChange = useCallback(
    (newFilters) => {
      setFilters(newFilters);

      // Clear existing timer
      if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
      }

      // If search filter changed, debounce the API call
      if (newFilters.search !== filters.search) {
        const timer = setTimeout(() => {
          fetchJobs(1, newFilters);
        }, 500); // 500ms debounce
        setSearchDebounceTimer(timer);
      } else {
        // For other filters, make immediate API call
        fetchJobs(1, newFilters);
      }
    },
    [filters, searchDebounceTimer, fetchJobs]
  );

  // Handle page changes
  const handlePageChange = useCallback(
    (page) => {
      fetchJobs(page, filters);
      // Scroll to top when page changes
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    [fetchJobs, filters]
  );

  // Initial data fetch
  useEffect(() => {
    fetchJobs(1);
    fetchStats();
  }, [fetchJobs, fetchStats]);

  // Update page title
  useEffect(() => {
    document.title = isInternshipPage
      ? "Internship Search - AdvisorAI"
      : "Job Search - AdvisorAI";
  }, [isInternshipPage]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
      }
    };
  }, [searchDebounceTimer]);

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

      {/* Main Content Area */}
      <div className="flex-1 flex relative overflow-hidden">
        {/* Sidebar - Between header and footer */}
        {sidebarOpen && (
          <div className="flex-shrink-0 z-40 relative">
            <Sidebar />
          </div>
        )}

        {/* Content - Takes remaining space */}
        <div className="flex-1 relative overflow-hidden">
          <div className="h-full bg-white/80 backdrop-blur-sm border-l border-slate-200/60">
            <div className="max-w-7xl mx-auto p-6 h-full overflow-y-auto">
              {/* Page Header */}
              <div className="mb-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-blue-100 rounded-xl">
                      <Briefcase className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h1 className="text-3xl font-bold text-gray-900">
                        {isInternshipPage ? "Internship Search" : "Job Search"}
                      </h1>
                      <p className="text-gray-600 mt-1">
                        Discover amazing{" "}
                        {isInternshipPage ? "internship" : "career"}{" "}
                        opportunities
                      </p>
                    </div>
                  </div>

                  {/* View Controls */}
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setShowFilters(!showFilters)}
                      className={`p-2 rounded-lg border transition-colors duration-200 ${
                        showFilters
                          ? "bg-blue-50 border-blue-200 text-blue-600"
                          : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
                      }`}
                      title="Toggle Filters"
                    >
                      <SlidersHorizontal className="w-5 h-5" />
                    </button>

                    <div className="flex items-center bg-white rounded-lg border border-gray-300 p-1">
                      <button
                        onClick={() => setViewMode("grid")}
                        className={`p-2 rounded-md transition-colors duration-200 ${
                          viewMode === "grid"
                            ? "bg-blue-50 text-blue-600"
                            : "text-gray-600 hover:bg-gray-50"
                        }`}
                        title="Grid View"
                      >
                        <Grid className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setViewMode("list")}
                        className={`p-2 rounded-md transition-colors duration-200 ${
                          viewMode === "list"
                            ? "bg-blue-50 text-blue-600"
                            : "text-gray-600 hover:bg-gray-50"
                        }`}
                        title="List View"
                      >
                        <List className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Results Summary */}
                {!loading && (
                  <div className="text-sm text-gray-600 bg-white rounded-lg px-4 py-2 inline-block border">
                    <span className="font-medium">
                      {pagination.total_items || 0}
                    </span>{" "}
                    {isInternshipPage ? "internships" : "jobs"} found
                    {Object.values(filters).some(
                      (filter) => filter && filter !== "all"
                    ) && (
                      <span className="ml-2 text-blue-600">
                        • Filters applied
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Main Content */}
              <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
                {/* Filters Sidebar */}
                {showFilters && (
                  <div className="xl:col-span-1">
                    <div className="sticky top-6">
                      <FilterPanel
                        filters={filters}
                        onFiltersChange={handleFiltersChange}
                        stats={stats}
                        type={pageType}
                        isLoading={loading}
                      />
                    </div>
                  </div>
                )}

                {/* Job Listings */}
                <div
                  className={`${
                    showFilters ? "xl:col-span-3" : "xl:col-span-4"
                  }`}
                >
                  {/* Loading State */}
                  {loading && (
                    <div className="flex items-center justify-center py-12">
                      <div className="text-center">
                        <Loader className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
                        <p className="text-gray-600">
                          Loading {isInternshipPage ? "internships" : "jobs"}...
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Error State */}
                  {error && !loading && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                      <AlertCircle className="w-8 h-8 text-red-600 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-red-900 mb-2">
                        Error Loading Data
                      </h3>
                      <p className="text-red-700 mb-4">{error}</p>
                      <button
                        onClick={() => fetchJobs(1)}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
                      >
                        Try Again
                      </button>
                    </div>
                  )}

                  {/* No Results */}
                  {!loading && !error && jobs.length === 0 && (
                    <div className="bg-gray-50 border border-gray-200 rounded-xl p-12 text-center">
                      <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">
                        No {isInternshipPage ? "Internships" : "Jobs"} Found
                      </h3>
                      <p className="text-gray-600 mb-6">
                        Try adjusting your filters or search criteria to find
                        more opportunities.
                      </p>
                      <button
                        onClick={() =>
                          handleFiltersChange({
                            search: "",
                            workModel: "all",
                            location: "",
                            companySize: "all",
                            industry: "",
                            ...(isInternshipPage
                              ? { hireTime: "" }
                              : { h1bSponsored: "all" }),
                          })
                        }
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200"
                      >
                        Clear All Filters
                      </button>
                    </div>
                  )}

                  {/* Job Cards */}
                  {!loading && !error && jobs.length > 0 && (
                    <>
                      <div
                        className={`job-grid ${
                          viewMode === "grid"
                            ? "grid grid-cols-1 lg:grid-cols-2 gap-6"
                            : "space-y-4"
                        }`}
                      >
                        {jobs.map((job, index) => (
                          <div
                            key={`${job.Apply || ""}-${index}`}
                            className="job-card"
                          >
                            <JobCard job={job} type={pageType} />
                          </div>
                        ))}
                      </div>

                      {/* Pagination */}
                      <div className="mt-8">
                        <Pagination
                          currentPage={pagination.current_page}
                          totalPages={pagination.total_pages}
                          onPageChange={handlePageChange}
                          itemsPerPage={pagination.per_page}
                          totalItems={pagination.total_items}
                          isLoading={loading}
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Footer */}
      <div className="flex-shrink-0 z-50 relative">
        <Footer />
      </div>
    </div>
  );
};

export default JobSearchPage;
