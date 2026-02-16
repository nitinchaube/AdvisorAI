import React, { useState } from "react";
import PageLayout from "./PageLayout";
import RatingPage from "./RatingPage";

const RatingsPageComponent = () => {
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      <div className="h-full w-full overflow-hidden">
        <RatingPage />
      </div>
    </PageLayout>
  );
};

export default RatingsPageComponent;
