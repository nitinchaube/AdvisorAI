import React from "react";
import { Heart, Github, Twitter, Linkedin, Mail } from "lucide-react";
import logo from "../utils/logo.png";

const Footer = () => {
  return (
    <footer className="bg-gradient-to-r from-slate-800 to-slate-700 backdrop-blur-xl border-t border-slate-600/20 px-6 py-4 shadow-2xl">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
          <div className="flex items-center space-x-2">
            <img src={logo} alt="AdvisorAI" className="w-5 h-5 object-contain" />
            <span className="text-sm text-slate-300 font-medium">
             Made by the AdvisorAI Team
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-slate-400">© 2024 AdvisorAI. All rights reserved.</span>
            <div className="flex items-center space-x-3">
              
              
              <a 
                href="mailto:nitinchaube08@gmail.com" 
                className="text-slate-400 hover:text-white transition-all duration-300 hover:scale-110 p-2 rounded-lg hover:bg-white/10"
                title="Contact us at nitinchaube08@gmail.com"
              >
                <Mail className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;