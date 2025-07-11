import React from "react";
import { NavLink } from "react-router-dom";
import reactLogo from "../assets/react.svg"; // Adjust path as needed

const Home = () => {
  return (
    <div>
      <div className="advisorai-overlay">
        <header className="advisorai-header redesigned">
          <img
            src={reactLogo}
            className="advisorai-logo"
            alt="AdvisorAI Logo"
          />
          <h1>
            Advisor<span className="ai-highlight">AI</span>
          </h1>
          <p className="advisorai-tagline">
            Empowering Students for Smarter Academic Choices
          </p>
          <div className="advisorai-auth-buttons">
            <NavLink to="/signup" className="advisorai-btn advisorai-signup">
              Sign Up
            </NavLink>
            <NavLink to="/login" className="advisorai-btn advisorai-login">
              Login
            </NavLink>
          </div>
        </header>
        <main className="advisorai-main redesigned">
          <section className="advisorai-section hero-section">
            <h2>Smarter Academic Planning Starts Here</h2>
            <p>
              Get personalized guidance for your coursework, university
              selection, and academic journey. Let AI help you make confident,
              informed decisions for your future.
            </p>
            <button className="advisorai-btn advisorai-cta-btn">
              Ask AdvisorAI
            </button>
          </section>
          <section className="advisorai-features redesigned">
            <div className="feature-card redesigned">
              <h3>Coursework Selection</h3>
              <p>
                Find the best courses tailored to your interests and career
                goals.
              </p>
            </div>
            <div className="feature-card redesigned">
              <h3>University Doubts</h3>
              <p>
                Get answers to your questions about universities, programs, and
                admissions.
              </p>
            </div>
            <div className="feature-card redesigned">
              <h3>Personalized Guidance</h3>
              <p>Receive AI-powered advice for your unique academic path.</p>
            </div>
          </section>
        </main>
        <footer className="advisorai-footer redesigned">
          <p>
            &copy; {new Date().getFullYear()} AdvisorAI. All rights reserved.
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Home;
