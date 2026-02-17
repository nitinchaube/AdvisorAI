import React from "react";
import { motion } from "framer-motion";
import { getThemeOptions } from "../utils/portfolioThemes";
import { Palette, Check } from "lucide-react";

const ThemeSelector = ({ selectedTheme, onThemeChange }) => {
  const themeOptions = getThemeOptions();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Palette className="w-6 h-6 text-slate-600" />
        <h3 className="text-xl font-semibold text-gray-900">Portfolio Theme</h3>
      </div>

      <p className="text-slate-600 mb-8">
        Choose a color theme that represents your personality and professional
        style.
      </p>

      <div className="theme-scroll-row">
        {themeOptions.map((theme) => (
          <motion.div
            key={theme.value}
            className={`theme-scroll-card relative cursor-pointer rounded-2xl border-2 transition-all duration-300 ${
              selectedTheme === theme.value
                ? "border-blue-500 ring-4 ring-blue-100"
                : "border-slate-200 hover:border-slate-300"
            }`}
            onClick={() => onThemeChange(theme.value)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Theme Preview */}
            <div className="p-6">
              {/* Color Palette Preview */}
              <div className="flex gap-2 mb-4">
                <div
                  className={`w-8 h-8 rounded-full bg-${theme.preview.primary}`}
                ></div>
                <div
                  className={`w-8 h-8 rounded-full bg-${theme.preview.secondary}`}
                ></div>
                <div
                  className={`w-8 h-8 rounded-full bg-${theme.preview.accent}`}
                ></div>
                <div
                  className={`w-8 h-8 rounded-full bg-${theme.preview.background}`}
                ></div>
              </div>

              {/* Theme Info */}
              <h4 className="font-semibold text-gray-900 mb-2">
                {theme.label}
              </h4>
              <p className="text-sm text-slate-600 mb-4">{theme.description}</p>

              {/* Mini Portfolio Preview */}
              <div
                className={`bg-${theme.preview.background} rounded-lg p-4 space-y-2`}
              >
                <div
                  className={`h-2 bg-${theme.preview.primary} rounded w-3/4`}
                ></div>
                <div
                  className={`h-1 bg-${theme.preview.secondary} rounded w-1/2`}
                ></div>
                <div className="flex gap-1">
                  <div
                    className={`h-1 bg-${theme.preview.accent} rounded w-1/4`}
                  ></div>
                  <div
                    className={`h-1 bg-${theme.preview.accent} rounded w-1/4`}
                  ></div>
                </div>
              </div>
            </div>

            {/* Selected Indicator */}
            {selectedTheme === theme.value && (
              <motion.div
                className="absolute top-3 right-3 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.2 }}
              >
                <Check className="w-4 h-4 text-white" />
              </motion.div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Theme Preview Section */}
      {selectedTheme && (
        <motion.div
          className="mt-8 p-6 bg-slate-50 rounded-2xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <h4 className="font-semibold text-gray-900 mb-3">
            Preview:{" "}
            {themeOptions.find((t) => t.value === selectedTheme)?.label}
          </h4>
          <p className="text-slate-600 text-sm mb-4">
            Your portfolio will use this color scheme. You can change it anytime
            in your profile settings.
          </p>

          {/* Live Preview Card */}
          <div
            className={`bg-${
              themeOptions.find((t) => t.value === selectedTheme)?.preview
                .background
            } rounded-xl p-6 border border-${
              themeOptions.find((t) => t.value === selectedTheme)?.preview
                .cardBorder
            }`}
          >
            <div className="flex items-center gap-4 mb-4">
              <div
                className={`w-12 h-12 bg-gradient-to-br from-${
                  themeOptions.find((t) => t.value === selectedTheme)?.preview
                    .skillBg
                } to-${
                  themeOptions.find((t) => t.value === selectedTheme)?.preview
                    .accent
                } rounded-xl flex items-center justify-center text-${
                  themeOptions.find((t) => t.value === selectedTheme)?.preview
                    .secondary
                } font-bold`}
              >
                JD
              </div>
              <div>
                <h5
                  className={`font-semibold text-${
                    themeOptions.find((t) => t.value === selectedTheme)?.preview
                      .textPrimary
                  }`}
                >
                  Your Name
                </h5>
                <p
                  className={`text-sm text-${
                    themeOptions.find((t) => t.value === selectedTheme)?.preview
                      .textSecondary
                  }`}
                >
                  Your Professional Title
                </p>
              </div>
            </div>
            <div
              className={`inline-flex items-center px-4 py-2 bg-${
                themeOptions.find((t) => t.value === selectedTheme)?.preview.cta
              } text-${
                themeOptions.find((t) => t.value === selectedTheme)?.preview
                  .ctaText
              } rounded-lg text-sm font-medium`}
            >
              Contact Me
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ThemeSelector;
