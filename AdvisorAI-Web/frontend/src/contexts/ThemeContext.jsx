import React, { createContext, useContext, useState, useEffect } from "react";
import { getWebsiteTheme } from "../utils/websiteThemes";

const ThemeContext = createContext();

export function useTheme() {
  return useContext(ThemeContext);
}

// Applies CSS variables for the given theme to the document root
function applyThemeVars(themeName) {
  const theme = getWebsiteTheme(themeName);
  const root = document.documentElement;
  Object.entries(theme.vars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
}

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState(
    () => localStorage.getItem("websiteTheme") || "blue"
  );

  // Apply theme on first render and whenever it changes
  useEffect(() => {
    applyThemeVars(currentTheme);
  }, [currentTheme]);

  const changeTheme = (themeName) => {
    setCurrentTheme(themeName);
    localStorage.setItem("websiteTheme", themeName);
    applyThemeVars(themeName);
  };

  return (
    <ThemeContext.Provider value={{ currentTheme, changeTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
