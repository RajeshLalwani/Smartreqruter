"use strict";

import React from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const GlassCard: React.FC<GlassCardProps> = ({ children, className, hover = true }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hover ? { scale: 1.02, transition: { duration: 0.2 } } : {}}
      className={cn(
        "relative rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl transition-all duration-300",
        hover && "hover:border-white/20 hover:shadow-[0_0_40px_rgba(255,255,255,0.05)]",
        className
      )}
    >
      {/* Gloss Effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
};
