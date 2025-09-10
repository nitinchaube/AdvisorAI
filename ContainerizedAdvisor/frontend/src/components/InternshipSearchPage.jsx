import React from "react";
import JobSearchPage from "./JobSearchPage";

// InternshipSearchPage is essentially the same as JobSearchPage
// The JobSearchPage component automatically detects if it's being used for internships
// based on the URL path and adjusts accordingly
const InternshipSearchPage = () => {
  return <JobSearchPage />;
};

export default InternshipSearchPage;
