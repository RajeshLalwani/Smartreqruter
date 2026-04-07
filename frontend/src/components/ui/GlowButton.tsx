"use strict";

import React from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface GlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  glowColor?: string;
}

export const GlowButton: React.FC<GlowButtonProps> = ({ 
  children, 
  className, 
  variant = 'primary',
  glowColor,
  ...props 
}) => {
  const variants = {
    primary: "border-cyan-500/50 bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500 hover:text-white",
    secondary: "border-purple-500/50 bg-purple-500/10 text-purple-400 hover:bg-purple-500 hover:text-white",
    danger: "border-rose-500/50 bg-rose-500/10 text-rose-400 hover:bg-rose-500 hover:text-white",
  };

  const glowColors = {
    primary: "rgba(6, 182, 212, 0.4)",
    secondary: "rgba(168, 85, 247, 0.4)",
    danger: "rgba(244, 63, 94, 0.4)",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.05, boxShadow: `0 0 20px ${glowColor || glowColors[variant]}` }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        "group relative flex items-center justify-center gap-2 rounded-xl border px-6 py-2.5 font-medium transition-all duration-300",
        variants[variant],
        className
      )}
      {...props}
    >
      <div className="relative z-10">{children}</div>
      <div className="absolute inset-0 -z-10 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </motion.button>
  );
};
