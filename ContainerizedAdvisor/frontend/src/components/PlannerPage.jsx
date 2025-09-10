import React, { useState } from "react";
import PageLayout from "./PageLayout";

const PlannerPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      <div>Planner Page</div>
    </PageLayout>
  );
};

export default PlannerPage;
