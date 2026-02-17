import React, { useState, useEffect } from "react";
import PageLayout from "./PageLayout";
import { Link } from "react-router-dom";
import {
  MessageCircle,
  TrendingUp,
  Clock,
  Zap,
  Search,
  Database,
  History,
  BarChart3,
  Calendar,
  Target,
  Award,
  Activity,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { apiService } from "../services/api";

const AnalyticsPage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const { currentUser } = useAuth();

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setAnalytics({
          chatUsage: {
            totalQuestions: 127,
            questionsThisWeek: 23,
            questionsThisMonth: 89,
            averageResponseTime: 2.3,
            totalSessions: 45,
            averageSessionLength: 8.5,
          },
          toolUsage: {
            webSearch: 67,
            chromaDatabase: 89,
            historyTool: 112,
            generalTool: 23,
          },
          quality: {
            averageReflectionScore: 8.2,
            refinementRate: 15,
            highQualityAnswers: 108,
          },
          topics: {
            courses: 34,
            professors: 28,
            admissions: 19,
            jobs: 15,
            internships: 12,
            other: 19,
          },
          engagement: {
            mostActiveDay: "Monday",
            mostActiveHour: "2 PM",
            followUpRate: 42,
            avgQuestionsPerSession: 2.8,
          },
        });
        setLoading(false);
      } catch (error) {
        console.error("Error fetching analytics:", error);
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  // ── Reusable sub-components ──────────────────────────────────────────────

  const StatCard = ({ icon: Icon, title, value, subtitle }) => (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200/60 p-6 hover:shadow-xl transition-all duration-300 hover:scale-[1.02]">
      <div className="flex items-center justify-between mb-4">
        <div
          className="p-3 rounded-xl text-white shadow-md"
          style={{
            background: `linear-gradient(to bottom right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
          }}
        >
          <Icon className="w-6 h-6" />
        </div>
        {subtitle && (
          <span className="text-xs text-slate-500 font-medium">{subtitle}</span>
        )}
      </div>
      <h3 className="text-2xl font-bold text-slate-900 mb-1">{value}</h3>
      <p className="text-sm text-slate-600">{title}</p>
    </div>
  );

  const ProgressBar = ({ label, value, max }) => {
    const percentage = (value / max) * 100;
    return (
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-slate-700">{label}</span>
          <span className="text-sm font-semibold text-slate-900">{value}</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2.5">
          <div
            className="h-2.5 rounded-full transition-all duration-500"
            style={{
              width: `${percentage}%`,
              background: `linear-gradient(to right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
            }}
          />
        </div>
      </div>
    );
  };

  // Section heading with themed icon
  const SectionHeading = ({ icon: Icon, children }) => (
    <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center">
      <div
        className="p-2 rounded-lg text-white mr-3"
        style={{
          background: `linear-gradient(to bottom right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
        }}
      >
        <Icon className="w-5 h-5" />
      </div>
      {children}
    </h2>
  );

  // ── Loading state ────────────────────────────────────────────────────────

  if (loading) {
    return (
      <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
        <div
          className="h-full w-full overflow-y-auto flex items-center justify-center"
          style={{
            background: `linear-gradient(to bottom right, var(--theme-page-bg-from), var(--theme-page-bg-via), var(--theme-page-bg-to))`,
          }}
        >
          <div className="text-center">
            <div
              className="w-16 h-16 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4"
              style={{ borderColor: `var(--theme-accent) transparent transparent transparent` }}
            />
            <p className="text-slate-600">Loading analytics...</p>
          </div>
        </div>
      </PageLayout>
    );
  }

  // ── Main render ──────────────────────────────────────────────────────────

  return (
    <PageLayout sidebarOpen={sidebarOpen} onMenuToggle={handleMenuToggle}>
      <div
        className="h-full w-full overflow-y-auto"
        style={{
          background: `linear-gradient(to bottom right, var(--theme-page-bg-from), var(--theme-page-bg-via), var(--theme-page-bg-to))`,
        }}
      >
        <div className="max-w-7xl mx-auto p-6 lg:p-8">

          {/* ── Page title ── */}
          <div className="mb-8">
            <h1
              className="text-4xl font-bold mb-2"
              style={{
                background: `linear-gradient(to right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Analytics Dashboard
            </h1>
            <p className="text-lg text-slate-700">
              Track your academic progress and chatbot usage insights
            </p>
          </div>

          {/* ── Profile management links ── */}
          <div className="bg-white rounded-3xl shadow-lg border border-slate-200/60 p-6 mb-8">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">
                    Profile Data
                  </h3>
                  <p className="text-slate-600">
                    View and edit all your profile information from the database
                  </p>
                </div>
                <Link
                  to="/profile-data"
                  className="text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg"
                  style={{
                    background: `linear-gradient(to right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
                  }}
                >
                  View Profile Data
                </Link>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">
                    Edit Profile
                  </h3>
                  <p className="text-slate-600">
                    Update your resume and profile information
                  </p>
                </div>
                <Link
                  to="/profile-completion"
                  className="text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg"
                  style={{
                    background: `linear-gradient(to right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
                  }}
                >
                  Edit Profile
                </Link>
              </div>
            </div>
          </div>

          {analytics && (
            <>
              {/* ── Chat Usage Stats ── */}
              <div className="mb-8">
                <SectionHeading icon={MessageCircle}>Chat Usage Analytics</SectionHeading>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <StatCard icon={MessageCircle} title="Total Questions Asked" value={analytics.chatUsage.totalQuestions} subtitle="All time" />
                  <StatCard icon={Activity} title="Questions This Week" value={analytics.chatUsage.questionsThisWeek} subtitle="Last 7 days" />
                  <StatCard icon={Calendar} title="Questions This Month" value={analytics.chatUsage.questionsThisMonth} subtitle="Last 30 days" />
                  <StatCard icon={Clock} title="Avg Response Time" value={`${analytics.chatUsage.averageResponseTime}s`} subtitle="Seconds" />
                  <StatCard icon={History} title="Total Sessions" value={analytics.chatUsage.totalSessions} subtitle="Chat sessions" />
                  <StatCard icon={Target} title="Avg Session Length" value={`${analytics.chatUsage.averageSessionLength}`} subtitle="Questions per session" />
                </div>
              </div>

              {/* ── Tool Usage ── */}
              <div className="mb-8">
                <SectionHeading icon={Zap}>Tool Usage Statistics</SectionHeading>
                <div className="bg-white rounded-2xl shadow-lg border border-slate-200/60 p-6">
                  <ProgressBar label="History Tool"     value={analytics.toolUsage.historyTool}     max={analytics.toolUsage.historyTool} />
                  <ProgressBar label="Chroma Database"  value={analytics.toolUsage.chromaDatabase}  max={analytics.toolUsage.historyTool} />
                  <ProgressBar label="Web Search"        value={analytics.toolUsage.webSearch}        max={analytics.toolUsage.historyTool} />
                  <ProgressBar label="General Tool"     value={analytics.toolUsage.generalTool}     max={analytics.toolUsage.historyTool} />
                </div>
              </div>

              {/* ── Quality Metrics ── */}
              <div className="mb-8">
                <SectionHeading icon={Award}>Answer Quality Metrics</SectionHeading>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatCard icon={TrendingUp} title="Avg Reflection Score" value={analytics.quality.averageReflectionScore} subtitle="Out of 10" />
                  <StatCard icon={BarChart3}  title="Refinement Rate"       value={`${analytics.quality.refinementRate}%`} subtitle="Answers improved" />
                  <StatCard icon={Award}      title="High Quality Answers"  value={analytics.quality.highQualityAnswers} subtitle="Score ≥ 8" />
                </div>
              </div>

              {/* ── Topic Distribution ── */}
              <div className="mb-8">
                <SectionHeading icon={Search}>Topic Distribution</SectionHeading>
                <div className="bg-white rounded-2xl shadow-lg border border-slate-200/60 p-6">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {[
                      { label: "Courses",      val: analytics.topics.courses },
                      { label: "Professors",   val: analytics.topics.professors },
                      { label: "Admissions",   val: analytics.topics.admissions },
                      { label: "Jobs",         val: analytics.topics.jobs },
                      { label: "Internships",  val: analytics.topics.internships },
                      { label: "Other",        val: analytics.topics.other },
                    ].map(({ label, val }) => (
                      <div
                        key={label}
                        className="text-center p-4 rounded-xl"
                        style={{
                          background: `var(--theme-accent-bg)`,
                          border: `1px solid var(--theme-sidebar-active-border)`,
                        }}
                      >
                        <div
                          className="text-3xl font-bold"
                          style={{
                            background: `linear-gradient(to right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
                            WebkitBackgroundClip: "text",
                            WebkitTextFillColor: "transparent",
                            backgroundClip: "text",
                          }}
                        >
                          {val}
                        </div>
                        <div className="text-sm text-slate-600 mt-1 font-medium">{label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ── Engagement Insights ── */}
              <div className="mb-8">
                <SectionHeading icon={Activity}>Engagement Insights</SectionHeading>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <StatCard icon={Calendar}      title="Most Active Day"    value={analytics.engagement.mostActiveDay} />
                  <StatCard icon={Clock}          title="Most Active Hour"   value={analytics.engagement.mostActiveHour} />
                  <StatCard icon={MessageCircle}  title="Follow-up Rate"     value={`${analytics.engagement.followUpRate}%`} subtitle="Questions with follow-ups" />
                  <StatCard icon={Target}         title="Questions/Session"  value={analytics.engagement.avgQuestionsPerSession} subtitle="Average" />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </PageLayout>
  );
};

export default AnalyticsPage;
