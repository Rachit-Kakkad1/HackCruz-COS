import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, MessageSquare, Clock3, Tag, Key } from 'lucide-react';

const RecallPopup = ({ isOpen, data, onClose }) => {
    // Handle ESC key press
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    return (
        <AnimatePresence>
            {isOpen && data && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
                    {/* Overlay */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-zinc-950/70 backdrop-blur-sm cursor-pointer"
                    />

                    {/* Modal content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="relative w-full max-w-lg glass-panel rounded-2xl overflow-hidden border border-white/10 shadow-2xl flex flex-col"
                        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
                    >
                        {/* Top decorative gradient */}
                        <div className="h-2 w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500" />

                        <div className="p-6">
                            {/* Header */}
                            <div className="flex items-start justify-between mb-6">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-xl bg-zinc-900 border border-white/5 flex items-center justify-center p-2 shadow-inner">
                                        <img src={data.favicon} alt="" className="w-full h-full object-contain" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-zinc-100 tracking-tight leading-tight pr-4">
                                            {data.title}
                                        </h2>
                                        <div className="flex items-center gap-2 mt-1.5 text-xs font-medium text-zinc-500">
                                            <span className="flex items-center gap-1"><Clock3 className="w-3.5 h-3.5" /> {data.timestamp}</span>
                                            <span className="w-1 h-1 rounded-full bg-zinc-700"></span>
                                            <span className="flex items-center gap-1 text-indigo-400 capitalize bg-indigo-500/10 px-1.5 py-0.5 rounded"><Tag className="w-3 h-3" /> {data.type}</span>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="p-2 -mr-2 -mt-2 text-zinc-400 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Summary Section */}
                            <div className="bg-zinc-900/50 rounded-xl p-5 border border-white/5 mb-6 shadow-inner">
                                <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                    <Key className="w-3.5 h-3.5" /> AI Recall Summary
                                </h3>
                                <p className="text-zinc-200 text-sm leading-relaxed">
                                    {data.summary}
                                </p>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-3">
                                <button className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white shadow hover:shadow-indigo-500/25 py-2.5 px-4 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2">
                                    <ExternalLink className="w-4 h-4" />
                                    Reopen Context
                                </button>
                                <button className="flex-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 py-2.5 px-4 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 border border-white/5">
                                    <MessageSquare className="w-4 h-4" />
                                    Chat with Context
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};

export default RecallPopup;
