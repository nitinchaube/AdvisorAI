import React from "react";
import { NavLink } from "react-router-dom";
import reactLogo from "../assets/react.svg";

const Home = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50">
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 relative">
        <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white text-center py-8 px-4">
          <img
            src={reactLogo}
            className="h-20 mx-auto mb-4 animate-spin"
            style={{ animationDuration: '20s' }}
            alt="AdvisorAI Logo"
          />
          <h1 className="text-4xl font-bold mb-2">
            Advisor<span className="text-yellow-400">AI</span>
          </h1>
          <p className="text-xl text-blue-100 mb-6">
            Empowering Students for Smarter Academic Choices
          </p>
          <div className="flex justify-center space-x-4">
            <NavLink 
              to="/signup" 
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Sign Up
            </NavLink>
            <NavLink 
              to="/login" 
              className="bg-transparent border-2 border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors"
            >
              Login
            </NavLink>
          </div>
        </header>
        
        <main className="max-w-6xl mx-auto px-4 py-12">
          <section className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Smarter Academic Planning Starts Here
            </h2>
            <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
              Get personalized guidance for your coursework, university
              selection, and academic journey. Let AI help you make confident,
              informed decisions for your future.
            </p>
            <NavLink 
              to="/dashboard"
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Ask AdvisorAI
            </NavLink>
          </section>
          
          <section className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="bg-white/10 backdrop-blur-sm p-8 rounded-2xl border border-white/20 hover:bg-white/20 transition-all duration-300">
              <h3 className="text-2xl font-bold text-white mb-4">Coursework Selection</h3>
              <p className="text-gray-300">
                Find the best courses tailored to your interests and career
                goals.
              </p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm p-8 rounded-2xl border border-white/20 hover:bg-white/20 transition-all duration-300">
              <h3 className="text-2xl font-bold text-white mb-4">University Doubts</h3>
              <p className="text-gray-300">
                Get answers to your questions about universities, programs, and
                admissions.
              </p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm p-8 rounded-2xl border border-white/20 hover:bg-white/20 transition-all duration-300">
              <h3 className="text-2xl font-bold text-white mb-4">Personalized Guidance</h3>
              <p className="text-gray-300">
                Receive AI-powered advice for your unique academic path.
              </p>
            </div>
          </section>
        </main>
        
        <footer className="text-center py-8 text-gray-400">
          <p>&copy; {new Date().getFullYear()} AdvisorAI. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
};

export default Home;
