import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, X } from 'lucide-react';
import { getExtensionUrl } from '../utils';

const FloatingWidget = ({ isOpen, onClick }) => {
    return (
        <motion.div
            className="fixed bottom-6 right-6 z-[10000] flex items-center justify-end pointer-events-auto"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 0.5 }}
        >
            <div className="relative group flex items-center">
                {/* Tooltip */}
                {!isOpen && (
                    <div className="mr-3 px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-200 text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap shadow-xl border border-white/10 hidden md:block">
                        Open COS
                    </div>
                )}

                {/* Glow behind button */}
                <div className="absolute inset-x-auto right-0 w-12 h-12 bg-indigo-500 blur-xl opacity-20 group-hover:opacity-50 transition-opacity duration-500 -z-10 rounded-full" />

                <motion.button
                    onClick={onClick}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-zinc-900 border border-white/10 hover:border-indigo-500/50 hover:bg-zinc-800 text-zinc-200 shadow-2xl transition-colors duration-300"
                    aria-label={isOpen ? "Close COS Panel" : "Open COS Panel"}
                >
                    <motion.div
                        initial={false}
                        animate={{ rotate: isOpen ? 180 : 0, scale: isOpen ? 0.8 : 1 }}
                        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                        className={!isOpen ? "overflow-hidden rounded-md flex items-center justify-center w-6 h-6" : ""}
                    >
                        {isOpen ? <X className="w-5 h-5 text-zinc-400" /> : <img src={getExtensionUrl("logo.png")} alt="COS Logo" className="w-full h-full object-cover" />}
                    </motion.div>
                </motion.button>
            </div>
        </motion.div>
    );
};

export default FloatingWidget;
