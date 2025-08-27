import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  MapPin,
  Building,
  Briefcase,
  Globe,
  Users,
  Calendar,
} from "lucide-react";

const FilterPanel = ({
  filters,
  onFiltersChange,
  stats = {},
  type = "job",
  isLoading = false,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState(filters);

  const isInternship = type === "internship";

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearAllFilters = () => {
    const clearedFilters = {
      search: "",
      workModel: "all",
      location: "",
      companySize: "all",
      industry: "",
      ...(isInternship ? { hireTime: "" } : { h1bSponsored: "all" }),
    };
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const getFilterCount = () => {
    let count = 0;
    if (localFilters.search) count++;
    if (localFilters.workModel !== "all") count++;
    if (localFilters.location) count++;
    if (localFilters.companySize !== "all") count++;
    if (localFilters.industry) count++;
    if (isInternship && localFilters.hireTime) count++;
    if (!isInternship && localFilters.h1bSponsored !== "all") count++;
    return count;
  };

  const formatStatLabel = (key, value) => {
    if (key === "company_sizes") {
      return value === "Unknown" ? "Not specified" : `${value} employees`;
    }
    return value === "Unknown" ? "Not specified" : value;
  };

  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Filter className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Filters{" "}
            {getFilterCount() > 0 && (
              <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {getFilterCount()}
              </span>
            )}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {getFilterCount() > 0 && (
            <button
              onClick={clearAllFilters}
              className="text-sm text-red-600 hover:text-red-700 font-medium flex items-center gap-1"
            >
              <X className="w-3 h-3" />
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-500 hover:text-gray-700 lg:hidden"
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Filter Content */}
      <div className={`space-y-6 ${!isExpanded ? "hidden lg:block" : ""}`}>
        {/* Search Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Search className="w-4 h-4 inline mr-2" />
            Search {isInternship ? "Internships" : "Jobs"}
          </label>
          <input
            type="text"
            value={localFilters.search || ""}
            onChange={(e) => handleFilterChange("search", e.target.value)}
            placeholder={`Search by title, company, location...`}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          />
        </div>

        {/* Work Model Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Globe className="w-4 h-4 inline mr-2" />
            Work Model
          </label>
          <select
            value={localFilters.workModel || "all"}
            onChange={(e) => handleFilterChange("workModel", e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          >
            <option value="all">All Work Models</option>
            {stats.work_models &&
              Object.entries(stats.work_models).map(([model, count]) => (
                <option key={model} value={model}>
                  {model} ({count})
                </option>
              ))}
          </select>
        </div>

        {/* Location Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="w-4 h-4 inline mr-2" />
            Location
          </label>
          <input
            type="text"
            value={localFilters.location || ""}
            onChange={(e) => handleFilterChange("location", e.target.value)}
            placeholder="Enter city, state, or country"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          />
        </div>

        {/* Company Size Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Users className="w-4 h-4 inline mr-2" />
            Company Size
          </label>
          <select
            value={localFilters.companySize || "all"}
            onChange={(e) => handleFilterChange("companySize", e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          >
            <option value="all">All Company Sizes</option>
            {stats.company_sizes &&
              Object.entries(stats.company_sizes)
                .sort(([a], [b]) => {
                  // Sort company sizes logically
                  const order = [
                    "1-10",
                    "11-50",
                    "51-200",
                    "201-500",
                    "501-1000",
                    "1001-5000",
                    "5001-10000",
                    "10000+",
                  ];
                  const aIndex = order.indexOf(a);
                  const bIndex = order.indexOf(b);
                  if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
                  if (aIndex !== -1) return -1;
                  if (bIndex !== -1) return 1;
                  return a.localeCompare(b);
                })
                .map(([size, count]) => (
                  <option key={size} value={size}>
                    {formatStatLabel("company_sizes", size)} ({count})
                  </option>
                ))}
          </select>
        </div>

        {/* Industry Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Briefcase className="w-4 h-4 inline mr-2" />
            Industry
          </label>
          <input
            type="text"
            value={localFilters.industry || ""}
            onChange={(e) => handleFilterChange("industry", e.target.value)}
            placeholder="Enter industry (e.g., Technology, Finance)"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
          />
        </div>

        {/* H1B Sponsorship Filter (Jobs only) */}
        {!isInternship && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Building className="w-4 h-4 inline mr-2" />
              H1B Sponsorship
            </label>
            <select
              value={localFilters.h1bSponsored || "all"}
              onChange={(e) =>
                handleFilterChange("h1bSponsored", e.target.value)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
            >
              <option value="all">All H1B Status</option>
              {stats.h1b_sponsorship &&
                Object.entries(stats.h1b_sponsorship).map(([status, count]) => (
                  <option key={status} value={status}>
                    {status === "not sure"
                      ? "Not Specified"
                      : status.charAt(0).toUpperCase() + status.slice(1)}{" "}
                    ({count})
                  </option>
                ))}
            </select>
          </div>
        )}

        {/* Hire Time Filter (Internships only) */}
        {isInternship && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Calendar className="w-4 h-4 inline mr-2" />
              Hiring Timeline
            </label>
            <input
              type="text"
              value={localFilters.hireTime || ""}
              onChange={(e) => handleFilterChange("hireTime", e.target.value)}
              placeholder="Enter hiring timeline (e.g., Summer 2026)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
            />
          </div>
        )}
      </div>

      {/* Stats Summary */}
      {!isLoading && stats && (
        <div className="mt-6 pt-6 border-t border-gray-100">
          <div className="text-sm text-gray-600">
            <div className="font-medium mb-2">Quick Stats:</div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                Total {isInternship ? "Internships" : "Jobs"}:{" "}
                {stats[`total_${isInternship ? "internships" : "jobs"}`] || 0}
              </div>
              {stats.work_models && (
                <div>Remote: {stats.work_models["Remote"] || 0}</div>
              )}
              {!isInternship && stats.h1b_sponsorship && (
                <div>H1B Sponsored: {stats.h1b_sponsorship["yes"] || 0}</div>
              )}
              {isInternship && stats.hire_times && (
                <div>
                  Summer 2026:{" "}
                  {Object.entries(stats.hire_times).find(([key]) =>
                    key.includes("2026-Summer")
                  )?.[1] || 0}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;
