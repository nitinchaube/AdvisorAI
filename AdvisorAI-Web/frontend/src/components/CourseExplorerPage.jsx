import React, { useState } from "react";
import PageLayout from "./PageLayout";
import CourseExplorer from "./CourseExplorer";
import CourseDetails from "./CourseDetails";
import ProfessorDetails from "./ProfessorDetails";

const CourseExplorerPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedCourseId, setSelectedCourseId] = useState(null);
  const [selectedProfessorId, setSelectedProfessorId] = useState(null);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSelect = (itemId, category) => {
    if (category === "course") {
      setSelectedCourseId(itemId);
      setSelectedProfessorId(null);
    } else if (category === "professor") {
      setSelectedProfessorId(itemId);
      setSelectedCourseId(null);
    }
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      {selectedProfessorId ? (
        <ProfessorDetails
          professorId={selectedProfessorId}
          onBack={() => setSelectedProfessorId(null)}
        />
      ) : selectedCourseId ? (
        <CourseDetails
          courseId={selectedCourseId}
          onBack={() => setSelectedCourseId(null)}
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
