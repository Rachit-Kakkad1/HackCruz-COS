import React from 'react';
import { motion } from 'framer-motion';
import { Network, Link } from 'lucide-react';

const ClusterView = () => {
    return (
        <div className="glass-card rounded-xl p-4 mt-4">
            <div className="flex items-center justify-between mb-3 border-b border-zinc-800/50 pb-2">
                <h3 className="text-xs font-semibold text-zinc-400 capitalize tracking-wider flex items-center gap-1.5">
                    <Network className="w-3.5 h-3.5 text-purple-400/80" /> Active Cluster
                </h3>
                <span className="text-[10px] text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded-full font-medium">Auto-grouped</span>
            </div>

            <div className="space-y-4 pt-1">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.5)] flex-shrink-0" />
                        <h4 className="text-sm font-medium text-zinc-200">AI Research Session</h4>
                    </div>
                    <p className="text-[11px] text-zinc-500 ml-4 mb-3 border-l 2 border-zinc-800 pl-3">
                        Analyzing RAG architectures across 3 context sources.
                    </p>

                    <div className="flex gap-2 ml-4">
                        <motion.div whileHover={{ y: -2 }} className="w-8 h-8 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center shadow-sm cursor-pointer hover:border-white/10 transition-colors tooltip relative group">
                            <img src="https://www.google.com/s2/favicons?domain=youtube.com&sz=64" alt="YouTube" className="w-4 h-4 object-contain" />
                            <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] bg-zinc-800 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">YouTube</div>
                        </motion.div>

                        <div className="flex items-center justify-center text-zinc-700">
                            <Link className="w-3 h-3" />
                        </div>

                        <motion.div whileHover={{ y: -2 }} className="w-8 h-8 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center shadow-sm cursor-pointer hover:border-white/10 transition-colors tooltip relative group">
                            <img src="https://www.google.com/s2/favicons?domain=docs.google.com&sz=64" alt="Docs" className="w-4 h-4 object-contain" />
                            <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] bg-zinc-800 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">Docs</div>
                        </motion.div>

                        <div className="flex items-center justify-center text-zinc-700">
                            <Link className="w-3 h-3" />
                        </div>

                        <motion.div whileHover={{ y: -2 }} className="w-8 h-8 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center shadow-sm cursor-pointer hover:border-white/10 transition-colors tooltip relative group">
                            <img src="https://www.google.com/s2/favicons?domain=github.com&sz=64" alt="GitHub" className="w-4 h-4 object-contain" />
                            <div className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] bg-zinc-800 text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">GitHub</div>
                        </motion.div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ClusterView;
