"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'midnight' | 'nebula' | 'stellar';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('midnight');

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <div className={`min-h-screen transition-colors duration-700 ${
        theme === 'midnight' ? 'bg-[#0a0b10] text-slate-100' : 
        theme === 'nebula' ? 'bg-[#1a1a2e] text-slate-200' : 'bg-[#0f172a] text-slate-50'
      }`}>
        {/* Ambient Glows */}
        <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-500/10 blur-[120px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-500/10 blur-[120px]" />
        </div>
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used within ThemeProvider");
  return context;
};
