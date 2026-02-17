// Website Theme System
// Global color themes that change the entire website's look and feel

export const websiteThemes = {
  blue: {
    name: "Ocean Blue",
    description: "The default professional blue theme",
    swatchColors: ["#1e293b", "#1e3a5f", "#4338ca"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #1e293b, #1e3a5f)",
      "--theme-accent": "#3b82f6",
      "--theme-accent-dark": "#2563eb",
      "--theme-accent-mid": "#60a5fa",
      "--theme-accent-light": "#bfdbfe",
      "--theme-accent-bg": "#eff6ff",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#eff6ff",
      "--theme-page-bg-to": "#eef2ff",
      "--theme-sidebar-active-from": "rgba(147, 197, 253, 0.2)",
      "--theme-sidebar-active-to": "rgba(103, 232, 249, 0.2)",
      "--theme-sidebar-active-border": "rgba(96, 165, 250, 0.6)",
      "--theme-sidebar-icon-from": "#60a5fa",
      "--theme-sidebar-icon-to": "#06b6d4",
      "--theme-orb-1": "rgba(191, 219, 254, 0.4)",
      "--theme-orb-2": "rgba(221, 214, 254, 0.4)",
      "--theme-orb-3": "rgba(199, 210, 254, 0.3)",
    },
  },

  emerald: {
    name: "Forest Emerald",
    description: "Fresh greens for a calm, focused experience",
    swatchColors: ["#022c22", "#064e3b", "#166534"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #022c22, #064e3b)",
      "--theme-accent": "#10b981",
      "--theme-accent-dark": "#059669",
      "--theme-accent-mid": "#34d399",
      "--theme-accent-light": "#a7f3d0",
      "--theme-accent-bg": "#ecfdf5",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#ecfdf5",
      "--theme-page-bg-to": "#f0fdf4",
      "--theme-sidebar-active-from": "rgba(110, 231, 183, 0.2)",
      "--theme-sidebar-active-to": "rgba(52, 211, 153, 0.2)",
      "--theme-sidebar-active-border": "rgba(52, 211, 153, 0.6)",
      "--theme-sidebar-icon-from": "#34d399",
      "--theme-sidebar-icon-to": "#059669",
      "--theme-orb-1": "rgba(167, 243, 208, 0.4)",
      "--theme-orb-2": "rgba(187, 247, 208, 0.4)",
      "--theme-orb-3": "rgba(167, 243, 208, 0.3)",
    },
  },

  violet: {
    name: "Royal Violet",
    description: "Creative and bold with rich purples",
    swatchColors: ["#1e1035", "#2e1065", "#4c1d95"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #1e1035, #2e1065)",
      "--theme-accent": "#8b5cf6",
      "--theme-accent-dark": "#7c3aed",
      "--theme-accent-mid": "#a78bfa",
      "--theme-accent-light": "#ddd6fe",
      "--theme-accent-bg": "#f5f3ff",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#f5f3ff",
      "--theme-page-bg-to": "#eef2ff",
      "--theme-sidebar-active-from": "rgba(196, 181, 253, 0.2)",
      "--theme-sidebar-active-to": "rgba(167, 139, 250, 0.2)",
      "--theme-sidebar-active-border": "rgba(167, 139, 250, 0.6)",
      "--theme-sidebar-icon-from": "#a78bfa",
      "--theme-sidebar-icon-to": "#7c3aed",
      "--theme-orb-1": "rgba(221, 214, 254, 0.4)",
      "--theme-orb-2": "rgba(237, 233, 254, 0.4)",
      "--theme-orb-3": "rgba(224, 231, 255, 0.3)",
    },
  },

  rose: {
    name: "Elegant Rose",
    description: "Sophisticated and modern with rose tones",
    swatchColors: ["#3b0012", "#4c0519", "#9f1239"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #3b0012, #4c0519)",
      "--theme-accent": "#f43f5e",
      "--theme-accent-dark": "#e11d48",
      "--theme-accent-mid": "#fb7185",
      "--theme-accent-light": "#fecdd3",
      "--theme-accent-bg": "#fff1f2",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#fff1f2",
      "--theme-page-bg-to": "#fdf2f8",
      "--theme-sidebar-active-from": "rgba(253, 164, 175, 0.2)",
      "--theme-sidebar-active-to": "rgba(251, 113, 133, 0.2)",
      "--theme-sidebar-active-border": "rgba(251, 113, 133, 0.6)",
      "--theme-sidebar-icon-from": "#fb7185",
      "--theme-sidebar-icon-to": "#e11d48",
      "--theme-orb-1": "rgba(254, 205, 211, 0.4)",
      "--theme-orb-2": "rgba(251, 207, 232, 0.4)",
      "--theme-orb-3": "rgba(252, 231, 243, 0.3)",
    },
  },

  amber: {
    name: "Warm Amber",
    description: "Energetic and warm with golden tones",
    swatchColors: ["#2c1003", "#451a03", "#92400e"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #2c1003, #451a03)",
      "--theme-accent": "#f59e0b",
      "--theme-accent-dark": "#d97706",
      "--theme-accent-mid": "#fbbf24",
      "--theme-accent-light": "#fde68a",
      "--theme-accent-bg": "#fffbeb",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#fffbeb",
      "--theme-page-bg-to": "#fef9c3",
      "--theme-sidebar-active-from": "rgba(252, 211, 77, 0.2)",
      "--theme-sidebar-active-to": "rgba(251, 191, 36, 0.2)",
      "--theme-sidebar-active-border": "rgba(251, 191, 36, 0.6)",
      "--theme-sidebar-icon-from": "#fbbf24",
      "--theme-sidebar-icon-to": "#d97706",
      "--theme-orb-1": "rgba(253, 230, 138, 0.4)",
      "--theme-orb-2": "rgba(254, 240, 138, 0.4)",
      "--theme-orb-3": "rgba(254, 215, 170, 0.3)",
    },
  },

  teal: {
    name: "Modern Teal",
    description: "Fresh and contemporary with teal accents",
    swatchColors: ["#021b1b", "#042f2e", "#0c4a6e"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #021b1b, #042f2e)",
      "--theme-accent": "#14b8a6",
      "--theme-accent-dark": "#0d9488",
      "--theme-accent-mid": "#2dd4bf",
      "--theme-accent-light": "#99f6e4",
      "--theme-accent-bg": "#f0fdfa",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#f0fdfa",
      "--theme-page-bg-to": "#ecfeff",
      "--theme-sidebar-active-from": "rgba(94, 234, 212, 0.2)",
      "--theme-sidebar-active-to": "rgba(45, 212, 191, 0.2)",
      "--theme-sidebar-active-border": "rgba(45, 212, 191, 0.6)",
      "--theme-sidebar-icon-from": "#2dd4bf",
      "--theme-sidebar-icon-to": "#0d9488",
      "--theme-orb-1": "rgba(153, 246, 228, 0.4)",
      "--theme-orb-2": "rgba(165, 243, 252, 0.4)",
      "--theme-orb-3": "rgba(125, 211, 252, 0.3)",
    },
  },

  indigo: {
    name: "Deep Indigo",
    description: "Professional and trustworthy with deep blues",
    swatchColors: ["#12103a", "#1e1b4b", "#1e3a8a"],
    vars: {
      "--theme-header-gradient": "linear-gradient(to right, #12103a, #1e1b4b)",
      "--theme-accent": "#6366f1",
      "--theme-accent-dark": "#4f46e5",
      "--theme-accent-mid": "#818cf8",
      "--theme-accent-light": "#c7d2fe",
      "--theme-accent-bg": "#eef2ff",
      "--theme-page-bg-from": "#f8fafc",
      "--theme-page-bg-via": "#eef2ff",
      "--theme-page-bg-to": "#ede9fe",
      "--theme-sidebar-active-from": "rgba(165, 180, 252, 0.2)",
      "--theme-sidebar-active-to": "rgba(129, 140, 248, 0.2)",
      "--theme-sidebar-active-border": "rgba(129, 140, 248, 0.6)",
      "--theme-sidebar-icon-from": "#818cf8",
      "--theme-sidebar-icon-to": "#4f46e5",
      "--theme-orb-1": "rgba(199, 210, 254, 0.4)",
      "--theme-orb-2": "rgba(221, 214, 254, 0.4)",
      "--theme-orb-3": "rgba(224, 231, 255, 0.3)",
    },
  },

  stevens: {
    name: "Stevens Crimson",
    description: "Stevens Institute of Technology — signature crimson & charcoal",
    swatchColors: ["#363d45", "#A32638", "#A32638"],
    vars: {
      // Header: solid dark charcoal — exactly like the Stevens top navigation bar
      "--theme-header-gradient": "#363d45",
      // Accent: exact Stevens red rgb(163, 38, 56) = #A32638
      "--theme-accent": "#A32638",
      "--theme-accent-dark": "#7B1B2A",
      "--theme-accent-mid": "#A32638",
      "--theme-accent-light": "#d9899a",
      "--theme-accent-bg": "#fdf0f2",
      // Page background: pure clean white — matches Stevens' content area
      "--theme-page-bg-from": "#ffffff",
      "--theme-page-bg-via": "#ffffff",
      "--theme-page-bg-to": "#ffffff",
      // Sidebar active: flat crimson tint, no gradient
      "--theme-sidebar-active-from": "rgba(163, 38, 56, 0.12)",
      "--theme-sidebar-active-to": "rgba(163, 38, 56, 0.12)",
      "--theme-sidebar-active-border": "rgba(163, 38, 56, 0.5)",
      // Icons: solid Stevens red, no gradient
      "--theme-sidebar-icon-from": "#A32638",
      "--theme-sidebar-icon-to": "#A32638",
      // Background orbs: barely visible so the white page stays clean
      "--theme-orb-1": "rgba(163, 38, 56, 0.04)",
      "--theme-orb-2": "rgba(163, 38, 56, 0.03)",
      "--theme-orb-3": "rgba(163, 38, 56, 0.04)",
    },
  },
};

// Get a single theme by key
export const getWebsiteTheme = (themeName = "blue") => {
  return websiteThemes[themeName] || websiteThemes.blue;
};

// Get all theme options for a selector UI
export const getWebsiteThemeOptions = () => {
  return Object.entries(websiteThemes).map(([key, theme]) => ({
    value: key,
    label: theme.name,
    description: theme.description,
    swatchColors: theme.swatchColors,
  }));
};
