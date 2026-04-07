"use strict";

import React from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

export const ThunderSpinner: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div className={cn("inline-flex items-center justify-center", className)}>
      <motion.div
        animate={{ 
          rotate: 360,
          scale: [1, 1.2, 1],
        }}
        transition={{ 
          rotate: { repeat: Infinity, duration: 1.5, ease: "linear" },
          scale: { repeat: Infinity, duration: 2, ease: "easeInOut" }
        }}
        className="relative h-12 w-12"
      >
        <svg viewBox="0 0 24 24" fill="none" className="h-full w-full stroke-cyan-400">
          <motion.path
            d="M13 2L3 14H12L11 22L21 10H12L13 2Z"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ 
                pathLength: { duration: 1.5, repeat: Infinity },
                opacity: { duration: 0.5 }
            }}
          />
        </svg>
        <div className="absolute inset-0 blur-lg bg-cyan-400/20 group-hover:bg-cyan-400/40 transition-colors rounded-full" />
      </motion.div>
    </div>
  );
};
