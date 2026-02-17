import React, { useState } from "react";
import { useTheme } from "../contexts/ThemeContext";
import { getWebsiteThemeOptions } from "../utils/websiteThemes";
import PageLayout from "./PageLayout";
import {
  Palette,
  CheckCircle,
  Monitor,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

const WebsiteThemePage = () => {
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);
  const { currentTheme, changeTheme } = useTheme();
  const [previewTheme, setPreviewTheme] = useState(currentTheme);
  const [saved, setSaved] = useState(false);

  const themeOptions = getWebsiteThemeOptions();

  const handleApply = () => {
    changeTheme(previewTheme);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <PageLayout
      sidebarOpen={sidebarOpen}
      onMenuToggle={() => setSidebarOpen((prev) => !prev)}
    >
      <div className="h-full overflow-y-auto">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-12">
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div
                className="p-2.5 rounded-xl shadow-md"
                style={{
                  background: `linear-gradient(to bottom right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
                }}
              >
                <Palette className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold text-slate-900">
                    Website Theme
                  </h1>
                  <span className="flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">
                    <ShieldCheck className="w-3 h-3" />
                    Admin Only
                  </span>
                </div>
                <p className="text-slate-500 text-sm mt-0.5">
                  Change the global color theme for the entire website. The
                  change applies instantly for all users.
                </p>
              </div>
            </div>
          </div>

          {/* Currently Active Banner */}
          <div
            className="flex items-center gap-3 px-5 py-3 rounded-2xl mb-8 border"
            style={{
              background: `linear-gradient(to right, var(--theme-sidebar-active-from), var(--theme-sidebar-active-to))`,
              borderColor: `var(--theme-sidebar-active-border)`,
            }}
          >
            <Monitor className="w-5 h-5 flex-shrink-0" style={{ color: `var(--theme-accent)` }} />
            <div>
              <span className="text-sm font-semibold text-slate-700">
                Current theme:&nbsp;
              </span>
              <span className="text-sm font-bold" style={{ color: `var(--theme-accent-dark)` }}>
                {themeOptions.find((t) => t.value === currentTheme)?.label ||
                  "Ocean Blue"}
              </span>
            </div>
            {saved && (
              <div className="ml-auto flex items-center gap-1.5 text-emerald-600 text-sm font-medium">
                <CheckCircle className="w-4 h-4" />
                Theme saved!
              </div>
            )}
          </div>

          {/* Theme Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
            {themeOptions.map((theme) => {
              const isSelected = previewTheme === theme.value;
              const isActive = currentTheme === theme.value;

              return (
                <button
                  key={theme.value}
                  onClick={() => setPreviewTheme(theme.value)}
                  className={`relative text-left rounded-2xl border-2 transition-all duration-300 overflow-hidden group hover:scale-[1.02] focus:outline-none ${
                    isSelected
                      ? "border-slate-900 ring-4 ring-slate-900/10 shadow-xl"
                      : "border-slate-200 hover:border-slate-300 shadow-sm hover:shadow-md"
                  }`}
                >
                  {/* Colour swatch header */}
                  <div
                    className="h-20 w-full flex items-end px-4 pb-3"
                    style={{
                      background: `linear-gradient(135deg, ${theme.swatchColors[0]} 0%, ${theme.swatchColors[1]} 50%, ${theme.swatchColors[2]} 100%)`,
                    }}
                  >
                    {/* Active badge */}
                    {isActive && (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white/20 text-white border border-white/30 backdrop-blur-sm">
                        Active
                      </span>
                    )}
                    {/* Selected checkmark */}
                    {isSelected && (
                      <div className="ml-auto">
                        <CheckCircle className="w-5 h-5 text-white drop-shadow" />
                      </div>
                    )}
                  </div>

                  {/* Theme info */}
                  <div className="bg-white px-4 py-3">
                    <h3 className="font-semibold text-slate-900 text-sm">
                      {theme.label}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                      {theme.description}
                    </p>

                    {/* Mini colour dots */}
                    <div className="flex gap-1.5 mt-3">
                      {theme.swatchColors.map((color, i) => (
                        <span
                          key={i}
                          className="w-4 h-4 rounded-full border border-white shadow-sm"
                          style={{ background: color }}
                        />
                      ))}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Live Preview Panel */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-8">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-700">
                Live Preview
              </span>
              <span className="text-xs text-slate-400 ml-1">
                — {themeOptions.find((t) => t.value === previewTheme)?.label}
              </span>
            </div>

            <div className="p-5 space-y-4">
              {/* Simulated header strip */}
              <div className="rounded-xl overflow-hidden shadow-md">
                <PreviewHeader themeKey={previewTheme} />
              </div>

              {/* Simulated page background with card */}
              <div
                className="rounded-xl p-4 flex gap-3"
                style={{
                  background: `linear-gradient(to right, ${
                    themeOptions.find((t) => t.value === previewTheme)
                      ?.swatchColors[2] || "#eef2ff"
                  }22, ${
                    themeOptions.find((t) => t.value === previewTheme)
                      ?.swatchColors[1] || "#bfdbfe"
                  }11)`,
                }}
              >
                <div className="bg-white rounded-xl flex-1 p-3 shadow-sm border border-slate-100">
                  <div className="h-2 bg-slate-200 rounded mb-2 w-3/4"></div>
                  <div className="h-2 bg-slate-100 rounded mb-2 w-full"></div>
                  <div className="h-2 bg-slate-100 rounded w-2/3"></div>
                </div>
                <div className="bg-white rounded-xl flex-1 p-3 shadow-sm border border-slate-100">
                  <div className="h-2 bg-slate-200 rounded mb-2 w-1/2"></div>
                  <div className="h-2 bg-slate-100 rounded mb-2 w-full"></div>
                  <div className="h-2 bg-slate-100 rounded w-3/4"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Apply Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleApply}
              disabled={previewTheme === currentTheme}
              className="flex items-center gap-2 px-8 py-3 rounded-2xl font-semibold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              style={{
                background:
                  previewTheme === currentTheme
                    ? "#94a3b8"
                    : `linear-gradient(to right, var(--theme-sidebar-icon-from), var(--theme-sidebar-icon-to))`,
              }}
            >
              <Palette className="w-4 h-4" />
              {previewTheme === currentTheme ? "Already Applied" : "Apply Theme"}
            </button>

            {previewTheme !== currentTheme && (
              <button
                onClick={() => setPreviewTheme(currentTheme)}
                className="text-sm text-slate-500 hover:text-slate-700 underline underline-offset-2 transition-colors"
              >
                Reset to current
              </button>
            )}
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

// ── Small helper component: simulated header bar for the preview ──
const PreviewHeader = ({ themeKey }) => {
  const options = getWebsiteThemeOptions();
  const theme = options.find((t) => t.value === themeKey);
  const colors = theme?.swatchColors || ["#1e293b", "#1e3a5f", "#4338ca"];

  return (
    <div
      className="flex items-center justify-between px-4 py-2.5"
      style={{
        background: `linear-gradient(to right, ${colors[0]}, ${colors[1]})`,
      }}
    >
      <div className="flex items-center gap-2">
        <div
          className="w-5 h-5 rounded-lg"
          style={{ background: `linear-gradient(135deg, ${colors[1]}, ${colors[2]})` }}
        />
        <span className="text-white text-xs font-bold">AdvisorAI</span>
      </div>
      <div className="flex gap-2">
        <div className="w-12 h-1.5 bg-white/20 rounded-full"></div>
        <div className="w-8 h-1.5 bg-white/20 rounded-full"></div>
        <div
          className="w-6 h-6 rounded-full"
          style={{ background: `linear-gradient(135deg, ${colors[1]}, ${colors[2]})` }}
        />
      </div>
    </div>
  );
};

export default WebsiteThemePage;
