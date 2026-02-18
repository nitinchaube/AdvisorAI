import React from "react";
import { Shield, Zap, Star } from "lucide-react";
import "./BenefitsSection.css";

const BenefitsSection = () => {
  const features = [
    {
      icon: <Shield className="benefit-icon" />,
      title: "AI-Powered Insights",
      description:
        "Get personalized academic guidance from advanced AI algorithms",
    },
    {
      icon: <Zap className="benefit-icon" />,
      title: "Instant Access",
      description: "Quick and secure access to your academic dashboard",
    },
    {
      icon: <Star className="benefit-icon" />,
      title: "Secure & Private",
      description: "Your data is protected with enterprise-grade security",
    },
  ];

  return (
    <div className="benefits-section">
      <div className="benefits-container">
        <div className="benefits-header">
          <h2 className="benefits-title">Why Choose <a href="https://advisoraii.web.app" target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'underline', textUnderlineOffset: '4px' }}>AdvisorAI</a></h2>
          <p className="benefits-subtitle">
            Join thousands of students making smarter academic decisions
          </p>
        </div>

        <div className="benefits-list">
          {features.map((feature, index) => (
            <div key={index} className="benefit-item">
              <div className="benefit-icon">{feature.icon}</div>
              <div className="benefit-content">
                <h3 className="benefit-title">{feature.title}</h3>
                <p className="benefit-description">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BenefitsSection;
