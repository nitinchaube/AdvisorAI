import React, { createContext, useContext, useState, useEffect } from "react";
import { getWebsiteTheme } from "../utils/websiteThemes";
import { fetchWebsiteTheme, saveWebsiteTheme } from "../services/api";

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
  // Start with localStorage cache for instant paint, then sync from server
  const [currentTheme, setCurrentTheme] = useState(
    () => localStorage.getItem("websiteTheme") || "blue"
  );
  const [loading, setLoading] = useState(true);

  // On mount: fetch the global theme from the backend (MongoDB)
  useEffect(() => {
    let cancelled = false;
    fetchWebsiteTheme()
      .then((serverTheme) => {
        if (!cancelled && serverTheme) {
          setCurrentTheme(serverTheme);
          localStorage.setItem("websiteTheme", serverTheme);
          applyThemeVars(serverTheme);
        }
      })
      .catch(() => {
        // If fetch fails, keep using localStorage value
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  // Apply theme on first render and whenever it changes
  useEffect(() => {
    applyThemeVars(currentTheme);
  }, [currentTheme]);

  /**
   * Change the theme.
   * @param {string} themeName
   * @param {boolean} persist  If true (default), also save to MongoDB via API.
   */
  const changeTheme = async (themeName, persist = true) => {
    setCurrentTheme(themeName);
    localStorage.setItem("websiteTheme", themeName);
    applyThemeVars(themeName);

    if (persist) {
      try {
        await saveWebsiteTheme(themeName);
      } catch (err) {
        console.error("Failed to persist theme to server:", err);
        // Theme is still applied locally even if API call fails
      }
    }
  };

  return (
    <ThemeContext.Provider value={{ currentTheme, changeTheme, loading }}>
      {children}
    </ThemeContext.Provider>
  );
}
