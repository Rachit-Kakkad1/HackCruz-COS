import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';

const mockChartData = [
    { label: 'YouTube', value: 45, color: 'bg-red-500/80' },
    { label: 'Gmail', value: 20, color: 'bg-indigo-500/80' },
    { label: 'Docs', value: 25, color: 'bg-blue-500/80' },
    { label: 'GitHub', value: 10, color: 'bg-zinc-500/80' },
];

const TimeGraph = () => {
    // Generate realistic looking SVG path for the line graph
    // The path should zig-zag to reflect varying activity
    const pathData = "M 0 40 Q 20 10, 40 30 T 80 15 T 120 35 T 160 10 T 200 25 T 240 5";

    return (
        <div className="flex-1 glass-card rounded-xl p-4 flex flex-col relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4 relative z-10">
                <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-zinc-400" />
                    <h3 className="text-sm font-semibold text-zinc-300">App Usage</h3>
                </div>
                <span className="text-xs text-zinc-500 font-medium tracking-wide">2h 14m</span>
            </div>

            {/* 2. MINI TIMEGRAPH (Animated SVG Stroke) */}
            <div className="w-full h-12 relative mb-4">
                {/* Subtle grid lines */}
                <div className="absolute inset-0 flex flex-col justify-between">
                    <div className="w-full border-t border-zinc-700/30"></div>
                    <div className="w-full border-t border-zinc-700/30"></div>
                    <div className="w-full border-t border-zinc-700/30 w-0"></div>
                </div>

                {/* Animated Line Graph SVG */}
                <svg className="w-full h-full overflow-visible" viewBox="0 0 240 50" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="lineColor" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.4" />
                            <stop offset="50%" stopColor="#818cf8" stopOpacity="1" />
                            <stop offset="100%" stopColor="#c084fc" stopOpacity="1" />
                        </linearGradient>
                        <linearGradient id="fillGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.15" />
                            <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
                        </linearGradient>
                    </defs>

                    {/* Fill underneath stroke */}
                    <motion.path
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5, duration: 1 }}
                        d={`${pathData} L 240 50 L 0 50 Z`}
                        fill="url(#fillGradient)"
                    />

                    {/* Animated Stroke */}
                    <motion.path
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 1 }}
                        transition={{ duration: 1.5, ease: "easeInOut", delay: 0.2 }}
                        d={pathData}
                        fill="none"
                        stroke="url(#lineColor)"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="drop-shadow-[0_0_8px_rgba(129,140,248,0.5)]"
                    />
                </svg>
            </div>

            <div className="space-y-3 relative z-10">
                {mockChartData.map((item, index) => (
                    <div key={item.label} className="space-y-1">
                        <div className="flex justify-between text-[11px] font-medium">
                            <span className="text-zinc-300">{item.label}</span>
                            <span className="text-zinc-500">{item.value}%</span>
                        </div>
                        {/* Base Bar */}
                        <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                            {/* Fill Bar */}
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${item.value}%` }}
                                transition={{ duration: 1, delay: 0.2 + index * 0.1, type: 'spring' }}
                                className={`h-full rounded-full ${item.color}`}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TimeGraph;
