import React from "react";
import { Heart, Github, Twitter, Linkedin, Mail } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-white/10 backdrop-blur-xl border-t border-white/20 px-6 py-4 shadow-2xl">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-purple-200 font-medium">
              Made with
            </span>
            <Heart className="w-4 h-4 text-rose-400 fill-current animate-pulse" />
            <span className="text-sm text-purple-200 font-medium">
              by the AdvisorAI Team
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-purple-300">© 2024 AdvisorAI. All rights reserved.</span>
            <div className="flex items-center space-x-3">
              <a 
                href="#" 
                className="text-purple-300 hover:text-white transition-all duration-300 hover:scale-110"
                title="GitHub"
              >
                <Github className="w-4 h-4" />
              </a>
              <a 
                href="#" 
                className="text-purple-300 hover:text-white transition-all duration-300 hover:scale-110"
                title="Twitter"
              >
                <Twitter className="w-4 h-4" />
              </a>
              <a 
                href="#" 
                className="text-purple-300 hover:text-white transition-all duration-300 hover:scale-110"
                title="LinkedIn"
              >
                <Linkedin className="w-4 h-4" />
              </a>
              <a 
                href="#" 
                className="text-purple-300 hover:text-white transition-all duration-300 hover:scale-110"
                title="Contact"
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