import React from 'react';
import { motion } from 'framer-motion';
import { MessageSquare } from 'lucide-react';

const TimelineCard = ({ data, onClick, index }) => {
    return (
        <motion.div
            variants={{
                hidden: { opacity: 0, y: 15 },
                visible: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
            }}
            whileHover={{ scale: 1.01 }}
            className="relative pl-8 group"
        >
            {/* Interactive Timeline dot */}
            <div className="absolute left-[3px] top-4 w-2 h-2 rounded-full bg-zinc-700 border-2 border-zinc-950 group-hover:bg-indigo-400 transition-colors shadow-[0_0_0_4px_rgba(9,9,11,1)] group-hover:shadow-[0_0_8px_rgba(129,140,248,0.8),0_0_0_4px_rgba(9,9,11,1)] z-10" />

            {/* 3. SMART HOVER INSIGHTS (Tooltip) */}
            <div className="absolute z-50 left-[calc(100%+12px)] top-0 w-48 opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-300 translate-x-[-10px] group-hover:translate-x-0">
                <div className="bg-zinc-800/90 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-2xl">
                    <h4 className="text-[11px] font-bold text-indigo-300 mb-2 uppercase tracking-wide">Context Insights</h4>
                    <div className="space-y-1.5">
                        <div className="flex justify-between text-[11px]">
                            <span className="text-zinc-400">Time Spent</span>
                            <span className="text-zinc-200 font-medium">12 min</span>
                        </div>
                        <div className="flex justify-between text-[11px]">
                            <span className="text-zinc-400">Switches</span>
                            <span className="text-zinc-200 font-medium">3</span>
                        </div>
                        <div className="flex justify-between text-[11px]">
                            <span className="text-zinc-400">Focus Level</span>
                            <span className="text-emerald-400 font-medium">High</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Card Content */}
            <div className="glass-card rounded-xl p-3 relative overflow-hidden group-hover:bg-zinc-800/60 group-hover:border-indigo-500/20">
                {/* Subtle highlight effect on hover */}
                <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/0 via-indigo-500/0 to-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                <div className="flex gap-3 relative z-10">
                    <div className="w-8 h-8 shrink-0 flex items-center justify-center rounded-lg bg-zinc-900 border border-white/5 overflow-hidden shadow-sm group-hover:border-indigo-500/30 transition-colors">
                        {data.favicon ? (
                            <img src={data.favicon} alt="" className="w-4 h-4 object-contain" />
                        ) : (
                            <span className="text-zinc-500 text-xs">UX</span>
                        )}
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-0.5">
                            <h3 className="text-[13px] font-semibold text-zinc-200 truncate group-hover:text-indigo-200 transition-colors">
                                {data.title}
                            </h3>
                            <span className="text-[10px] text-zinc-500 font-medium shrink-0 pt-0.5 mt-auto mb-auto bg-zinc-900/50 px-1.5 rounded">
                                {data.timestamp}
                            </span>
                        </div>

                        <p className="text-xs text-zinc-400 leading-relaxed line-clamp-2 mb-3">
                            {data.summary}
                        </p>

                        {/* 5. RECALL BUTTON (Wow Feature) */}
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={onClick}
                            className="bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-300 text-[11px] font-semibold px-3 py-1.5 rounded-md flex items-center gap-1.5 border border-indigo-500/20 transition-colors w-max"
                        >
                            <MessageSquare className="w-3 h-3" />
                            Recall Context
                        </motion.button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default TimelineCard;
