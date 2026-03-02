import React, { useState } from "react";
import {
  MapPin,
  Building,
  Users,
  Calendar,
  ExternalLink,
  DollarSign,
  Briefcase,
  Globe,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const JobCard = ({ job, type = "job" }) => {
  const isInternship = type === "internship";
  const [isQualificationsExpanded, setIsQualificationsExpanded] =
    useState(false);

  // Helper function to format salary
  const formatSalary = (salary) => {
    if (!salary || salary === "N/A" || salary === "")
      return "Salary not specified";
    return salary;
  };

  // Helper function to truncate text
  const truncateText = (text, maxLength = 150) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  // Helper function to check if text needs truncation
  const needsTruncation = (text, maxLength = 200) => {
    return text && text.length > maxLength;
  };

  // Helper function to get H1B status color
  const getH1BStatusColor = (status) => {
    if (!status || status === "not sure") return "text-gray-500";
    if (status.toLowerCase() === "yes") return "text-green-600";
    if (status.toLowerCase() === "no") return "text-red-600";
    return "text-gray-500";
  };

  // Helper function to get H1B status icon
  const getH1BStatusIcon = (status) => {
    if (!status || status === "not sure") return null;
    if (status.toLowerCase() === "yes")
      return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (status.toLowerCase() === "no")
      return <XCircle className="w-4 h-4 text-red-600" />;
    return null;
  };

  return (
    <div className="bg-white rounded-lg sm:rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 hover:border-blue-200 p-4 sm:p-6 group w-full min-w-0 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3 sm:gap-0 mb-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg sm:text-xl font-semibold text-gray-900 group-hover:text-blue-600 transition-colors duration-200 line-clamp-2">
            {job["Position Title"] || "Position Title Not Available"}
          </h3>
          <div className="flex items-center gap-2 mt-2 min-w-0">
            <Building className="w-4 h-4 text-gray-500 flex-shrink-0" />
            <span className="text-gray-700 font-medium flex-1 min-w-0 break-words">
              {job.Company || "Company Not Specified"}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-start sm:items-end gap-2 w-full sm:w-auto">
          {job.Date && (
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Calendar className="w-3 h-3 flex-shrink-0" />
              <span className="break-words">
                {new Date(job.Date).toLocaleDateString()}
              </span>
            </div>
          )}
          {job.Apply && (
            <a
              href={job.Apply}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-1 px-3 py-2 sm:py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium w-full sm:w-auto"
            >
              Apply <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* Key Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 mb-4">
        <div className="space-y-3 min-w-0">
          {/* Location */}
          {job.Location && (
            <div className="flex items-start gap-2 text-sm min-w-0">
              <MapPin className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
              <span className="text-gray-600 min-w-0 break-words">
                {job.Location}
              </span>
            </div>
          )}

          {/* Work Model */}
          {job["Work Model"] && (
            <div className="flex items-center gap-2 text-sm">
              <Globe className="w-4 h-4 text-gray-500" />
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  job["Work Model"].toLowerCase() === "remote"
                    ? "bg-green-100 text-green-800"
                    : job["Work Model"].toLowerCase() === "on site"
                    ? "bg-blue-100 text-blue-800"
                    : "bg-yellow-100 text-yellow-800"
                }`}
              >
                {job["Work Model"]}
              </span>
            </div>
          )}

          {/* Company Size */}
          {job["Company Size"] && (
            <div className="flex items-center gap-2 text-sm">
              <Users className="w-4 h-4 text-gray-500" />
              <span className="text-gray-600">
                {job["Company Size"]} employees
              </span>
            </div>
          )}
        </div>

        <div className="space-y-3 min-w-0">
          {/* Salary */}
          {(job.Salary || isInternship) && (
            <div className="flex items-center gap-2 text-sm">
              <DollarSign className="w-4 h-4 text-gray-500" />
              <span className="text-gray-600 font-medium">
                {formatSalary(job.Salary)}
              </span>
            </div>
          )}

          {/* Industry */}
          {job["Company Industry"] && (
            <div className="flex items-start gap-2 text-sm min-w-0">
              <Briefcase className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
              <span className="text-gray-600 min-w-0 break-words">
                {job["Company Industry"]}
              </span>
            </div>
          )}

          {/* H1B Sponsorship (for jobs) or Hire Time (for internships) */}
          {!isInternship && job["H1b Sponsored"] && (
            <div className="flex items-center gap-2 text-sm">
              {getH1BStatusIcon(job["H1b Sponsored"])}
              <span className="text-gray-500">H1B:</span>
              <span
                className={`font-medium ${getH1BStatusColor(
                  job["H1b Sponsored"]
                )}`}
              >
                {job["H1b Sponsored"]}
              </span>
            </div>
          )}

          {isInternship && job["Hire Time"] && (
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-gray-600">
                Hiring for: {job["Hire Time"]}
              </span>
            </div>
          )}

          {isInternship && job["Graduate Time"] && (
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-gray-600">
                Graduate: {job["Graduate Time"]}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Qualifications */}
      {job.Qualifications && (
        <div className="border-t border-gray-100 pt-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            Qualifications
          </h4>
          <div className="text-sm text-gray-600 leading-relaxed">
            <p className="whitespace-pre-line">
              {isQualificationsExpanded
                ? job.Qualifications
                : truncateText(job.Qualifications, 200)}
            </p>
            {needsTruncation(job.Qualifications, 200) && (
              <button
                onClick={() =>
                  setIsQualificationsExpanded(!isQualificationsExpanded)
                }
                className="inline-flex items-center gap-1 mt-2 text-blue-600 hover:text-blue-700 font-medium text-sm transition-colors duration-200"
              >
                {isQualificationsExpanded ? (
                  <>
                    Read Less <ChevronUp className="w-4 h-4" />
                  </>
                ) : (
                  <>
                    Read More <ChevronDown className="w-4 h-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* New Grad Badge */}
      {job["Is New Grad"] && job["Is New Grad"].toLowerCase() === "yes" && (
        <div className="mt-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            New Grad Friendly
          </span>
        </div>
      )}
    </div>
  );
};

export default JobCard;