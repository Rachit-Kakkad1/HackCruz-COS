import React from 'react';
import { motion } from 'framer-motion';
import { Target, TrendingUp } from 'lucide-react';

const FocusScore = () => {
    const score = 82;
    const radius = 36;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (score / 100) * circumference;

    return (
        <div className="glass-card rounded-xl p-4 flex flex-col items-center justify-center relative overflow-hidden group">
            {/* Background mesh/glow */}
            <div className="absolute inset-0 bg-gradient-to-b from-indigo-500/5 to-transparent pointer-events-none" />

            <div className="flex w-full justify-between items-start absolute top-4 left-4 right-4 text-zinc-400">
                <Target className="w-4 h-4 opacity-50" />
                <TrendingUp className="w-4 h-4 text-emerald-400/80" />
            </div>

            <div className="relative flex items-center justify-center mt-2">
                <svg className="w-24 h-24 transform -rotate-90">
                    {/* Background Circle */}
                    <circle
                        cx="48"
                        cy="48"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="6"
                        fill="transparent"
                        className="text-zinc-800"
                    />
                    {/* Foreground Animated Circle */}
                    <motion.circle
                        cx="48"
                        cy="48"
                        r={radius}
                        stroke="currentColor"
                        strokeWidth="6"
                        fill="transparent"
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset }}
                        transition={{ duration: 1.5, ease: "easeOut", delay: 0.1 }}
                        className="text-indigo-500 drop-shadow-[0_0_8px_rgba(99,102,241,0.5)]"
                        strokeLinecap="round"
                    />
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-zinc-100">{score}</span>
                    <span className="text-[10px] text-zinc-500 uppercase font-bold tracking-wider">%</span>
                </div>
            </div>

            <h3 className="text-xs font-semibold text-zinc-400 mt-3 pt-2 border-t border-white/5 w-full text-center">Focus Score</h3>
        </div>
    );
};

export default FocusScore;
