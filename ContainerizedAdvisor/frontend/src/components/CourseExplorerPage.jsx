import React, { useState, useEffect } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import PageLayout from "./PageLayout";
import CourseExplorer from "./CourseExplorer";
import CourseDetails from "./CourseDetails";
import ProfessorDetails from "./ProfessorDetails";

const CourseExplorerPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { professorId, courseId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSelect = (itemId, category) => {
    if (category === "course") {
      navigate(`/course/${itemId}${location.search}`);
    } else if (category === "professor") {
      navigate(`/professor/${itemId}${location.search}`);
    }
  };

  const handleBack = () => {
    // Navigate back to course explorer with preserved search state
    navigate(`/course-explorer${location.search}`);
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      {professorId ? (
        <ProfessorDetails
          professorId={professorId}
          onBack={handleBack}
        />
      ) : courseId ? (
        <CourseDetails
          courseId={courseId}
          onBack={handleBack}
        />
      ) : (
        <div className="h-full w-full overflow-hidden">
          <CourseExplorer onSelectCourse={handleSelect} />
        </div>
      )}
    </PageLayout>
  );
};

export default CourseExplorerPage;
