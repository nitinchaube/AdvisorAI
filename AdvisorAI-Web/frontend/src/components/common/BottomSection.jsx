import React from "react";
import { CheckCircle } from "lucide-react";
import "./BottomSection.css";

const BottomSection = () => {
  const features = [
    "AI-Powered Course Recommendations",
    "Personalized Academic Planning",
    "24/7 AI Support & Guidance",
    "Career Path Optimization"
  ];

  return (
    <div className="bottom-section">
      <div className="features-preview">
        <h3 className="features-title">What You'll Get</h3>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-item">
              <CheckCircle className="feature-icon" />
              <span>{feature}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="stats-preview">
        <div className="stat-item">
          <div className="stat-number">10K+</div>
          <div className="stat-label">Students</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">95%</div>
          <div className="stat-label">Satisfaction</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">24/7</div>
          <div className="stat-label">Support</div>
        </div>
      </div>
    </div>
  );
};

export default BottomSection;
