import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  MapPin,
  Globe,
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
    };
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const getFilterCount = () => {
    let count = 0;
    if (localFilters.search) count++;
    if (localFilters.workModel !== "all") count++;
    if (localFilters.location) count++;
    return count;
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;
