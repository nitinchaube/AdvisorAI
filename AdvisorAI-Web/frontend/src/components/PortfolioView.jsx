import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiService } from "../services/api";
import {
  Mail,
  MapPin,
  Github,
  Linkedin,
  Briefcase,
  GraduationCap,
  ExternalLink,
  Download,
  ArrowRight,
} from "lucide-react";
import { motion } from "framer-motion";
import { getTheme, getThemeClasses } from "../utils/portfolioThemes";

// Helper for avatar initials
const getInitials = (name) => {
  if (!name) return "?";
  const parts = name.split(" ");
  return parts.length === 1
    ? parts[0][0].toUpperCase()
    : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
};

// Enhanced Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 60 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.25, 0.25, 0.25, 0.75],
    },
  },
};

const fadeInLeft = {
  hidden: { opacity: 0, x: -60 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.6,
      ease: [0.25, 0.25, 0.25, 0.75],
    },
  },
};

const fadeInRight = {
  hidden: { opacity: 0, x: 60 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.6,
      ease: [0.25, 0.25, 0.25, 0.75],
    },
  },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const scaleOnHover = {
  hover: {
    scale: 1.02,
    transition: { duration: 0.2 },
  },
};

const cardHover = {
  hover: {
    y: -8,
    boxShadow:
      "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    transition: { duration: 0.3 },
  },
};

const PortfolioView = () => {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await apiService.getPublicProfile(userId);
        if (res.success && res.profile) {
          setProfile(res.profile);
        } else {
          setError("Profile not found or not public.");
        }
      } catch (e) {
        setError("Failed to load portfolio.");
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [userId]);

  // Theme system - with fallback loading state
  const userTheme = profile?.portfolioTheme || "slate";
  const theme = getTheme(userTheme);
  const themeClasses = getThemeClasses(userTheme);

  if (loading)
    return (
      <div
        className={`min-h-screen flex items-center justify-center ${themeClasses.mainBg}`}
      >
        <div className={`text-2xl ${themeClasses.textSecondary}`}>
          Loading portfolio...
        </div>
      </div>
    );
  if (error)
    return (
      <div
        className={`min-h-screen flex items-center justify-center ${themeClasses.mainBg}`}
      >
        <div className="text-2xl text-red-500">{error}</div>
      </div>
    );
  if (!profile) return null;

  // Tagline: use summary first sentence or fallback
  const tagline = profile.summary
    ? profile.summary.split(". ")[0] + "."
    : "Turning ideas into impact.";

  // Socials
  const github = profile.github || (profile.socials && profile.socials.github);
  const linkedin =
    profile.linkedin || (profile.socials && profile.socials.linkedin);

  // Categorize skills
  const groupedSkills = {
    Languages: [],
    "Frameworks & Libraries": [],
    Databases: [],
    Tools: [],
  };

  (profile.skills || []).forEach((skill) => {
    const lower = skill.toLowerCase().trim();
    const skillWords = lower.split(" ");

    // Programming Languages
    if (
      [
        "javascript",
        "js",
        "python",
        "java",
        "c++",
        "cpp",
        "c",
        "c#",
        "csharp",
        "typescript",
        "ts",
        "go",
        "golang",
        "ruby",
        "php",
        "sql",
        "html",
        "css",
        "swift",
        "kotlin",
        "rust",
        "scala",
        "r",
      ].includes(lower) ||
      skillWords.some((word) => ["javascript", "python", "java"].includes(word))
    ) {
      groupedSkills.Languages.push(skill);
    }
    // Frameworks & Libraries
    else if (
      [
        "react",
        "reactjs",
        "vue",
        "vuejs",
        "vue.js",
        "angular",
        "angularjs",
        "node",
        "nodejs",
        "node.js",
        "express",
        "expressjs",
        "django",
        "flask",
        "spring",
        "spring boot",
        "laravel",
        "nextjs",
        "next.js",
        "nuxt",
        "nuxtjs",
        "svelte",
        "jquery",
        "bootstrap",
        "tailwind",
        "tailwindcss",
        "material-ui",
        "mui",
        "unity",
        "flutter",
        "react native",
      ].includes(lower) ||
      skillWords.some((word) =>
        [
          "react",
          "vue",
          "angular",
          "node",
          "express",
          "django",
          "flask",
        ].includes(word)
      )
    ) {
      groupedSkills["Frameworks & Libraries"].push(skill);
    }
    // Databases
    else if (
      [
        "mongodb",
        "mongo",
        "postgresql",
        "postgres",
        "mysql",
        "sqlite",
        "redis",
        "firebase",
        "firestore",
        "dynamodb",
        "oracle",
        "sql server",
        "sqlserver",
        "cassandra",
        "elasticsearch",
        "toad",
      ].includes(lower) ||
      skillWords.some((word) =>
        ["mongodb", "mysql", "postgresql", "redis", "firebase"].includes(word)
      )
    ) {
      groupedSkills.Databases.push(skill);
    }
    // Tools & Technologies
    else if (
      [
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "docker",
        "kubernetes",
        "k8s",
        "jenkins",
        "aws",
        "amazon web services",
        "azure",
        "microsoft azure",
        "gcp",
        "google cloud",
        "google cloud platform",
        "vscode",
        "visual studio code",
        "android studio",
        "xcode",
        "intellij",
        "webstorm",
        "pycharm",
        "vim",
        "neovim",
        "sublime text",
        "atom",
        "windows",
        "linux",
        "ubuntu",
        "centos",
        "macos",
        "mac os",
        "sap",
        "sap brim",
        "sap fica",
        "sap brim/fica",
        "jira",
        "confluence",
        "slack",
        "teams",
        "figma",
        "sketch",
        "adobe xd",
        "photoshop",
        "illustrator",
        "webpack",
        "vite",
        "parcel",
        "babel",
        "eslint",
        "prettier",
        "jest",
        "cypress",
        "selenium",
        "postman",
        "insomnia",
        "terraform",
        "ansible",
        "nginx",
        "apache",
        "linux",
        "bash",
        "shell",
        "powershell",
      ].includes(lower) ||
      skillWords.some((word) =>
        ["git", "docker", "aws", "azure", "linux", "windows"].includes(word)
      )
    ) {
      groupedSkills.Tools.push(skill);
    }
    // If none match, try to categorize based on common patterns
    else {
      // If it ends with common framework suffixes
      if (
        lower.endsWith("js") ||
        lower.endsWith(".js") ||
        lower.includes("framework")
      ) {
        groupedSkills["Frameworks & Libraries"].push(skill);
      }
      // If it contains database-related terms
      else if (
        lower.includes("db") ||
        lower.includes("database") ||
        lower.includes("sql")
      ) {
        groupedSkills.Databases.push(skill);
      }
      // Default to Tools instead of Languages for unknown items
      else {
        groupedSkills.Tools.push(skill);
      }
    }
  });

  return (
    <div
      className={`${themeClasses.mainBg} min-h-screen font-['Inter',system-ui,sans-serif] ${themeClasses.textPrimary}`}
    >
      {/* Hero Section - Asymmetrical Layout */}
      <section
        className={`min-h-screen relative bg-gradient-to-br ${themeClasses.mainBg} via-white to-${themeClasses.mainBg} overflow-hidden`}
      >
        {/* Background Elements */}
        <div
          className={`absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] ${themeClasses.accent} via-transparent to-transparent opacity-70`}
        ></div>
        <div
          className={`absolute top-10 right-10 w-72 h-72 ${themeClasses.accent} rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-pulse`}
        ></div>
        <div
          className={`absolute bottom-10 left-10 w-96 h-96 ${themeClasses.accent} rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse delay-300`}
        ></div>

        <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-12 gap-12 min-h-screen items-center">
            {/* Left Column - Text Content */}
            <motion.div
              className="lg:col-span-7 space-y-8 pt-20 lg:pt-0"
              variants={fadeInLeft}
              initial="hidden"
              animate="visible"
            >
              <div className="space-y-4">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2, duration: 0.6 }}
                  className={`inline-flex items-center px-4 py-2 rounded-full ${themeClasses.accent} ${themeClasses.textSecondary} text-sm font-medium`}
                >
                  👋 Hello, I'm
                </motion.div>

                <motion.h1
                  className="text-5xl lg:text-7xl font-bold tracking-tight leading-tight"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.8 }}
                >
                  <span className={themeClasses.textPrimary}>
                    {profile.fullName?.split(" ")[0]}
                  </span>
                  <br />
                  <span className={themeClasses.textSecondary}>
                    {profile.fullName?.split(" ").slice(1).join(" ")}
                  </span>
                </motion.h1>

                <motion.p
                  className={`text-xl lg:text-2xl ${themeClasses.textSecondary} leading-relaxed max-w-2xl`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.6 }}
                >
                  {tagline}
                </motion.p>
              </div>

              {/* Meta Information */}
              <motion.div
                className={`flex flex-wrap gap-6 ${themeClasses.textMuted}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7, duration: 0.6 }}
              >
                {profile.location && (
                  <div className="flex items-center gap-2">
                    <MapPin size={18} />
                    <span>{profile.location}</span>
                  </div>
                )}
                {profile.email && (
                  <div className="flex items-center gap-2">
                    <Mail size={18} />
                    <span>{profile.email}</span>
                  </div>
                )}
              </motion.div>

              {/* CTA Buttons */}
              <motion.div
                className="flex flex-wrap gap-4 pt-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9, duration: 0.6 }}
              >
                {profile.email && (
                  <motion.a
                    href={`mailto:${profile.email}`}
                    className={`inline-flex items-center px-8 py-4 ${themeClasses.cta} ${themeClasses.ctaText} rounded-lg font-semibold ${themeClasses.ctaHover} transition-all duration-300 group`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Let's Connect
                    <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </motion.a>
                )}

                <motion.button
                  className={`inline-flex items-center px-8 py-4 border-2 ${themeClasses.accentBorder} ${themeClasses.textSecondary} rounded-lg font-semibold ${themeClasses.cardBorderHover} ${themeClasses.accentHover} transition-all duration-300`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Download className="mr-2 w-4 h-4" />
                  Resume
                </motion.button>
              </motion.div>

              {/* Social Links */}
              <motion.div
                className="flex gap-6 pt-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.1, duration: 0.6 }}
              >
                {github && (
                  <motion.a
                    href={github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-12 h-12 flex items-center justify-center rounded-xl bg-white shadow-md text-slate-600 hover:text-slate-900 hover:shadow-lg transition-all duration-300"
                    whileHover={{ y: -2 }}
                  >
                    <Github size={20} />
                  </motion.a>
                )}
                {linkedin && (
                  <motion.a
                    href={linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-12 h-12 flex items-center justify-center rounded-xl bg-white shadow-md text-slate-600 hover:text-slate-900 hover:shadow-lg transition-all duration-300"
                    whileHover={{ y: -2 }}
                  >
                    <Linkedin size={20} />
                  </motion.a>
                )}
              </motion.div>
            </motion.div>

            {/* Right Column - Avatar/Visual */}
            <motion.div
              className="lg:col-span-5 flex justify-center lg:justify-end"
              variants={fadeInRight}
              initial="hidden"
              animate="visible"
            >
              <motion.div
                className="relative"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.8, ease: "easeOut" }}
              >
                <div
                  className={`w-80 h-80 lg:w-96 lg:h-96 rounded-2xl bg-gradient-to-br from-slate-50 to-slate-300 flex items-center justify-center text-6xl lg:text-7xl font-bold ${themeClasses.textSecondary} shadow-2xl relative overflow-hidden`}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                  <span className="relative z-10">
                    {getInitials(profile.fullName)}
                  </span>
                </div>

                {/* Floating Elements */}
                <motion.div
                  className={`absolute -top-4 -right-4 w-8 h-8 ${themeClasses.accent} rounded-full`}
                  animate={{ y: [0, -10, 0] }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                />
                <motion.div
                  className={`absolute -bottom-2 -left-2 w-6 h-6 ${themeClasses.secondaryBg} rounded-full`}
                  animate={{ y: [0, -15, 0] }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 1,
                  }}
                />
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* About Section */}
      {profile.summary && (
        <section className="py-20 lg:py-32 relative">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="grid lg:grid-cols-12 gap-12 items-center">
              <motion.div
                className="lg:col-span-5"
                variants={fadeInLeft}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-100px" }}
              >
                <div className="space-y-6">
                  <h2
                    className={`text-4xl lg:text-5xl font-bold tracking-tight ${themeClasses.textPrimary}`}
                  >
                    About <span className={themeClasses.textSecondary}>Me</span>
                  </h2>
                  <div
                    className={`w-20 h-1 ${themeClasses.accent} rounded-full`}
                  ></div>
                </div>
              </motion.div>

              <motion.div
                className="lg:col-span-7"
                variants={fadeInRight}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-100px" }}
              >
                <div className="prose prose-lg prose-slate max-w-none">
                  <p
                    className={`text-xl leading-relaxed ${themeClasses.textSecondary} font-light`}
                  >
                    {profile.summary}
                  </p>
                </div>
              </motion.div>
            </div>
          </div>
        </section>
      )}

      {/* Experience Section */}
      {profile.experience && profile.experience.length > 0 && (
        <section className={`py-20 lg:py-32 ${themeClasses.cardBg}`}>
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            {/* Section Header */}
            <motion.div
              className="text-center mb-20"
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              <h2
                className={`text-4xl lg:text-5xl font-bold tracking-tight mb-6 ${themeClasses.textPrimary}`}
              >
                Work{" "}
                <span className={themeClasses.textSecondary}>Experience</span>
              </h2>
              <div
                className={`w-20 h-1 ${themeClasses.accent} rounded-full mx-auto mb-6`}
              ></div>
              <p
                className={`text-xl ${themeClasses.textSecondary} max-w-2xl mx-auto`}
              >
                My professional journey and the impact I've made
              </p>
            </motion.div>

            {/* Timeline */}
            <div className="relative max-w-6xl mx-auto">
              {/* Timeline Line */}
              <div
                className={`absolute left-8 lg:left-1/2 lg:transform lg:-translate-x-1/2 h-full w-0.5 ${themeClasses.accent}`}
              ></div>

              <motion.div
                className="space-y-12"
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-100px" }}
              >
                {profile.experience.map((exp, idx) => (
                  <motion.div
                    key={idx}
                    className={`relative flex flex-col lg:flex-row ${
                      idx % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"
                    } items-start lg:items-center gap-8 lg:gap-12`}
                    variants={fadeInUp}
                  >
                    {/* Timeline Dot */}
                    <div
                      className={`absolute left-8 lg:left-1/2 lg:transform lg:-translate-x-1/2 w-4 h-4 ${themeClasses.secondaryBg} rounded-full border-4 border-white shadow-md z-10`}
                    ></div>

                    {/* Content Card */}
                    <motion.div
                      className={`flex-1 ml-20 lg:ml-0 ${
                        idx % 2 === 0 ? "lg:pr-12" : "lg:pl-12"
                      }`}
                      variants={cardHover}
                      whileHover="hover"
                    >
                      <div
                        className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} rounded-2xl p-8 shadow-sm hover:shadow-xl transition-all duration-300`}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex-1">
                            <h3
                              className={`text-2xl font-bold ${themeClasses.textPrimary} mb-2`}
                            >
                              {exp.position || exp.title}
                            </h3>
                            <p
                              className={`text-lg font-semibold ${themeClasses.textSecondary} mb-1`}
                            >
                              {exp.company}
                            </p>
                          </div>
                          <div
                            className={`w-12 h-12 ${themeClasses.skillBg} rounded-xl flex items-center justify-center`}
                          >
                            <Briefcase
                              className={`w-6 h-6 ${themeClasses.textSecondary}`}
                            />
                          </div>
                        </div>

                        <div className="mb-6">
                          <span
                            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${themeClasses.skillBg} ${themeClasses.textSecondary}`}
                          >
                            {exp.period ||
                              `${exp.startDate || ""} - ${
                                exp.endDate || "Present"
                              }`}
                          </span>
                        </div>

                        <p
                          className={`${themeClasses.textSecondary} leading-relaxed`}
                        >
                          {exp.description}
                        </p>
                      </div>
                    </motion.div>

                    {/* Spacer for alternating layout */}
                    <div
                      className={`hidden lg:block flex-1 ${
                        idx % 2 === 0 ? "lg:pl-12" : "lg:pr-12"
                      }`}
                    ></div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </div>
        </section>
      )}

      {/* Projects Section */}
      {profile.projects && profile.projects.length > 0 && (
        <section className={`py-20 lg:py-32 ${themeClasses.skillBg}`}>
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            {/* Section Header */}
            <motion.div
              className="text-center mb-20"
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              <h2
                className={`text-4xl lg:text-5xl font-bold tracking-tight mb-6 ${themeClasses.textPrimary}`}
              >
                Featured{" "}
                <span className={themeClasses.textSecondary}>Projects</span>
              </h2>
              <div
                className={`w-20 h-1 ${themeClasses.accent} rounded-full mx-auto mb-6`}
              ></div>
              <p
                className={`text-xl ${themeClasses.textSecondary} max-w-2xl mx-auto`}
              >
                A showcase of my latest work and creative solutions
              </p>
            </motion.div>

            {/* Projects Grid */}
            <motion.div
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 justify-items-center max-w-6xl mx-auto"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              {profile.projects.map((proj, idx) => (
                <motion.div
                  key={idx}
                  className="group w-full max-w-sm"
                  variants={fadeInUp}
                >
                  <motion.div
                    className={`${themeClasses.cardBg} rounded-2xl border ${themeClasses.cardBorder} shadow-sm hover:shadow-2xl transition-all duration-500 overflow-hidden h-full w-full`}
                    variants={cardHover}
                    whileHover="hover"
                  >
                    {/* Project Image Placeholder */}
                    <div
                      className={`h-48 bg-gradient-to-br from-slate-50 to-slate-300 relative overflow-hidden`}
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
                      <div className="absolute bottom-4 right-4 flex gap-2">
                        {proj.github && (
                          <motion.a
                            href={proj.github}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`w-10 h-10 bg-white/90 backdrop-blur-sm rounded-lg flex items-center justify-center ${themeClasses.textSecondary} hover:${themeClasses.textPrimary} hover:bg-white transition-all duration-200`}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            <Github size={18} />
                          </motion.a>
                        )}
                        {proj.url && (
                          <motion.a
                            href={proj.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`w-10 h-10 bg-white/90 backdrop-blur-sm rounded-lg flex items-center justify-center ${themeClasses.textSecondary} hover:${themeClasses.textPrimary} hover:bg-white transition-all duration-200`}
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            <ExternalLink size={18} />
                          </motion.a>
                        )}
                      </div>
                    </div>

                    {/* Project Content */}
                    <div className="p-8">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3
                            className={`text-2xl font-bold ${themeClasses.textPrimary} mb-2 group-hover:${themeClasses.textSecondary} transition-colors`}
                          >
                            {proj.name || proj.title}
                          </h3>
                          {proj.date && (
                            <span
                              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${themeClasses.skillBg} ${themeClasses.textSecondary}`}
                            >
                              {proj.date}
                            </span>
                          )}
                        </div>
                      </div>

                      <p
                        className={`${themeClasses.textSecondary} leading-relaxed mb-6`}
                      >
                        {proj.description}
                      </p>

                      {/* Project Links */}
                      <div
                        className={`flex gap-4 pt-4 border-t ${themeClasses.skillBorder}`}
                      >
                        {proj.github && (
                          <a
                            href={proj.github}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`inline-flex items-center ${themeClasses.textSecondary} hover:${themeClasses.textPrimary} font-medium transition-colors group`}
                          >
                            <Github className="mr-2 w-4 h-4 group-hover:scale-110 transition-transform" />
                            GitHub
                          </a>
                        )}
                        {proj.url && (
                          <a
                            href={proj.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`inline-flex items-center ${themeClasses.textSecondary} hover:${themeClasses.textPrimary} font-medium transition-colors group`}
                          >
                            <ExternalLink className="mr-2 w-4 h-4 group-hover:scale-110 transition-transform" />
                            Live Demo
                          </a>
                        )}
                      </div>
                    </div>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
      )}

      {/* Skills Section */}
      {profile.skills && profile.skills.length > 0 && (
        <section className={`py-20 lg:py-32 ${themeClasses.cardBg}`}>
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            {/* Section Header */}
            <motion.div
              className="text-center mb-20"
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              <h2
                className={`text-4xl lg:text-5xl font-bold tracking-tight mb-6 ${themeClasses.textPrimary}`}
              >
                Skills &{" "}
                <span className={themeClasses.textSecondary}>Expertise</span>
              </h2>
              <div
                className={`w-20 h-1 ${themeClasses.accent} rounded-full mx-auto mb-6`}
              ></div>
              <p
                className={`text-xl ${themeClasses.textSecondary} max-w-2xl mx-auto`}
              >
                Technologies and tools I work with to bring ideas to life
              </p>
            </motion.div>

            {/* Skills Grid */}
            <div className="flex justify-center">
              <motion.div
                className="grid gap-8 justify-items-center"
                style={{
                  gridTemplateColumns: `repeat(${
                    Object.entries(groupedSkills).filter(
                      ([_, skills]) => skills.length > 0
                    ).length
                  }, minmax(0, 320px))`,
                }}
                variants={staggerContainer}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-100px" }}
              >
                {Object.entries(groupedSkills).map(
                  ([category, skills]) =>
                    skills.length > 0 && (
                      <motion.div
                        key={category}
                        className="group w-full"
                        variants={fadeInUp}
                      >
                        <div
                          className={`${themeClasses.skillBg} rounded-2xl p-8 h-full border ${themeClasses.skillBorder} ${themeClasses.skillBorderHover} hover:${themeClasses.cardBg} transition-all duration-300 w-full`}
                        >
                          <div className="mb-6">
                            <h3
                              className={`text-xl font-bold ${themeClasses.textPrimary} mb-2`}
                            >
                              {category}
                            </h3>
                            <div
                              className={`w-12 h-1 ${themeClasses.accent} rounded-full group-hover:${themeClasses.secondaryBg} transition-colors`}
                            ></div>
                          </div>

                          <div className="flex flex-wrap gap-2">
                            {skills.map((skill, i) => (
                              <motion.span
                                key={i}
                                className={`px-4 py-2 ${themeClasses.skillPill} ${themeClasses.textSecondary} rounded-xl text-sm font-medium border ${themeClasses.skillPillBorder} ${themeClasses.cardBorderHover} hover:shadow-sm transition-all duration-200`}
                                whileHover={{ scale: 1.05, y: -2 }}
                                transition={{ duration: 0.2 }}
                              >
                                {skill}
                              </motion.span>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )
                )}
              </motion.div>
            </div>
          </div>
        </section>
      )}

      {/* Education Section */}
      {profile.education && profile.education.length > 0 && (
        <section className={`py-20 lg:py-32 ${themeClasses.skillBg}`}>
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            {/* Section Header */}
            <motion.div
              className="text-center mb-20"
              variants={fadeInUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              <h2
                className={`text-4xl lg:text-5xl font-bold tracking-tight mb-6 ${themeClasses.textPrimary}`}
              >
                Education &{" "}
                <span className={themeClasses.textSecondary}>Learning</span>
              </h2>
              <div
                className={`w-20 h-1 ${themeClasses.accent} rounded-full mx-auto mb-6`}
              ></div>
              <p
                className={`text-xl ${themeClasses.textSecondary} max-w-2xl mx-auto`}
              >
                My academic journey and continuous learning path
              </p>
            </motion.div>

            {/* Education Grid */}
            <motion.div
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 justify-items-center max-w-6xl mx-auto"
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              {profile.education.map((edu, idx) => (
                <motion.div
                  key={idx}
                  className="group w-full max-w-sm"
                  variants={fadeInUp}
                >
                  <motion.div
                    className={`${themeClasses.cardBg} rounded-2xl border ${themeClasses.cardBorder} shadow-sm hover:shadow-xl transition-all duration-300 p-8 h-full w-full`}
                    variants={cardHover}
                    whileHover="hover"
                  >
                    <div className="flex items-start justify-between mb-6">
                      <div
                        className={`w-16 h-16 ${themeClasses.skillBg} rounded-2xl flex items-center justify-center group-hover:${themeClasses.accent} transition-colors`}
                      >
                        <GraduationCap
                          className={`w-8 h-8 ${themeClasses.textSecondary}`}
                        />
                      </div>
                    </div>

                    <h3
                      className={`text-xl font-bold ${themeClasses.textPrimary} mb-3`}
                    >
                      {edu.degree || edu.title}
                    </h3>
                    <p
                      className={`text-lg font-semibold ${themeClasses.textSecondary} mb-3`}
                    >
                      {edu.institution}
                    </p>
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${themeClasses.skillBg} ${themeClasses.textSecondary}`}
                    >
                      {edu.period ||
                        `${edu.startDate || ""} - ${edu.endDate || ""}`}
                    </span>
                  </motion.div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>
      )}

      {/* Contact Section */}
      <section
        className={`py-20 lg:py-32 ${themeClasses.contactBg} text-white relative overflow-hidden`}
      >
        {/* Background Elements */}
        <div className="absolute inset-0">
          <div
            className={`absolute top-0 left-1/4 w-96 h-96 ${themeClasses.primaryBg} rounded-full mix-blend-multiply filter blur-xl opacity-50`}
          ></div>
          <div
            className={`absolute bottom-0 right-1/4 w-96 h-96 ${themeClasses.secondaryBg} rounded-full mix-blend-multiply filter blur-xl opacity-30`}
          ></div>
        </div>

        <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid lg:grid-cols-12 gap-12 items-center">
            {/* Left Column - Text Content */}
            <motion.div
              className="lg:col-span-7 space-y-8"
              variants={fadeInLeft}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              <div className="space-y-6">
                <h2 className="text-4xl lg:text-6xl font-bold tracking-tight leading-tight text-white">
                  Let's Build Something
                  <br />
                  <span className="text-slate-300">Amazing Together</span>
                </h2>

                <p className="text-xl text-slate-200 leading-relaxed max-w-2xl">
                  I'm always excited to work on new projects and collaborate
                  with talented people. Let's discuss how we can bring your
                  ideas to life.
                </p>
              </div>

              {/* Contact Info */}
              <div className="space-y-4">
                {profile.email && (
                  <div className="flex items-center gap-4 text-slate-200">
                    <div
                      className={`w-12 h-12 ${themeClasses.primaryBg} rounded-xl flex items-center justify-center`}
                    >
                      <Mail size={20} />
                    </div>
                    <span className="text-lg">{profile.email}</span>
                  </div>
                )}
                {profile.location && (
                  <div className="flex items-center gap-4 text-slate-200">
                    <div
                      className={`w-12 h-12 ${themeClasses.primaryBg} rounded-xl flex items-center justify-center`}
                    >
                      <MapPin size={20} />
                    </div>
                    <span className="text-lg">{profile.location}</span>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Right Column - CTA */}
            <motion.div
              className="lg:col-span-5 space-y-8"
              variants={fadeInRight}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
            >
              {/* Main CTA */}
              {profile.email && (
                <motion.a
                  href={`mailto:${profile.email}`}
                  className="block w-full"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="bg-white text-slate-900 rounded-2xl p-8 text-center hover:bg-slate-50 transition-all duration-300 group">
                    <Mail
                      className={`w-12 h-12 mx-auto mb-4 group-hover:scale-110 transition-transform ${themeClasses.cta}`}
                    />
                    <h3
                      className={`text-2xl font-bold mb-2 ${themeClasses.textPrimary}`}
                    >
                      Send me an email
                    </h3>
                    <p className={`${themeClasses.textSecondary} mb-4`}>
                      I usually respond within 24 hours
                    </p>
                    <div
                      className={`inline-flex items-center ${themeClasses.textPrimary} font-semibold group-hover:gap-3 gap-2 transition-all`}
                    >
                      Get in touch
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </motion.a>
              )}

              {/* Social Links */}
              <div className="flex gap-4 justify-center lg:justify-start">
                {github && (
                  <motion.a
                    href={github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`w-16 h-16 ${themeClasses.primaryBg} rounded-2xl flex items-center justify-center text-slate-300 hover:text-white ${themeClasses.primaryHoverBg} transition-all duration-300`}
                    whileHover={{ y: -4, scale: 1.05 }}
                  >
                    <Github size={24} />
                  </motion.a>
                )}
                {linkedin && (
                  <motion.a
                    href={linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`w-16 h-16 ${themeClasses.primaryBg} rounded-2xl flex items-center justify-center text-slate-300 hover:text-white ${themeClasses.primaryHoverBg} transition-all duration-300`}
                    whileHover={{ y: -4, scale: 1.05 }}
                  >
                    <Linkedin size={24} />
                  </motion.a>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        className={`py-8 ${themeClasses.footerBg} text-slate-400 border-t ${themeClasses.primaryBorder}`}
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm">
              © {new Date().getFullYear()} {profile.fullName}. All rights
              reserved.
            </p>
            <p className="text-sm">Crafted with ❤️ and modern technology</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PortfolioView;
