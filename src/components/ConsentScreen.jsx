import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Check } from 'lucide-react';
import { getExtensionUrl } from '../utils';

const ConsentScreen = ({ onConsentGranted }) => {
    const [isChecked, setIsChecked] = useState(false);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col h-full bg-zinc-900/60 p-6 z-50 overflow-y-auto w-full absolute inset-0 backdrop-blur-md"
        >
            <div className="flex flex-col items-center flex-1 justify-center mt-8">
                {/* Privacy Badge Identity */}
                <motion.div
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.1, type: "spring", stiffness: 200 }}
                    className="w-20 h-20 rounded-2xl bg-black/40 border border-white/5 flex items-center justify-center mb-6 shadow-2xl overflow-hidden"
                >
                    <img src={getExtensionUrl("logo.png")} alt="COS Logo" className="w-full h-full object-contain" />
                </motion.div>

                {/* Headers */}
                <h2 className="text-2xl font-bold text-zinc-100 tracking-tight mb-3">Welcome to COS</h2>
                <p className="text-sm text-zinc-400 text-center leading-relaxed max-w-sm mb-8">
                    COS helps you stay focused by analyzing your activity context locally on your device.
                </p>

                {/* Privacy Bullet Points */}
                <div className="w-full max-w-sm space-y-4 mb-10">
                    <div className="glass-card p-4 rounded-xl border border-white/5 bg-white/5 flex flex-col gap-3">
                        <div className="flex items-start gap-3">
                            <div className="mt-0.5 w-4 h-4 rounded-full bg-indigo-500/20 flex-shrink-0 flex items-center justify-center">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                            </div>
                            <span className="text-sm text-zinc-300">Only reads your active tab context</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-0.5 w-4 h-4 rounded-full bg-indigo-500/20 flex-shrink-0 flex items-center justify-center">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                            </div>
                            <span className="text-sm text-zinc-300">Runs 100% locally on your device</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-0.5 w-4 h-4 rounded-full bg-indigo-500/20 flex-shrink-0 flex items-center justify-center">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                            </div>
                            <span className="text-sm text-zinc-300">No screen recording or external logging</span>
                        </div>
                        <div className="flex items-start gap-3">
                            <div className="mt-0.5 w-4 h-4 rounded-full bg-indigo-500/20 flex-shrink-0 flex items-center justify-center">
                                <div className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                            </div>
                            <span className="text-sm text-zinc-300">No personal data stored on our servers</span>
                        </div>
                        <div className="flex items-start gap-3 pt-2 border-t border-white/10 mt-1">
                            <Shield className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-emerald-100 font-medium tracking-wide">You stay entirely in control.</span>
                        </div>
                    </div>
                </div>

                {/* Checkbox Accord */}
                <label className="flex items-center gap-3 cursor-pointer group mb-8 w-full max-w-sm px-2 relative">
                    <input
                        type="checkbox"
                        className="peer sr-only"
                        checked={isChecked}
                        onChange={(e) => setIsChecked(e.target.checked)}
                    />
                    <div className="w-6 h-6 shrink-0 rounded-md border-2 border-zinc-600 bg-zinc-800/50 peer-checked:bg-indigo-500 peer-checked:border-indigo-500 transition-all flex items-center justify-center group-hover:border-indigo-400">
                        {isChecked && (
                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}>
                                <Check className="w-4 h-4 text-white" strokeWidth={3} />
                            </motion.div>
                        )}
                    </div>
                    <span className="text-sm text-zinc-300 select-none group-hover:text-zinc-100 transition-colors">
                        I understand and agree to the terms
                    </span>
                    {/* Focus Ring representation for a11y */}
                    <div className="absolute inset-0 -m-1 rounded-lg pointer-events-none peer-focus-visible:ring-2 ring-indigo-500/50 opacity-0 peer-focus-visible:opacity-100" />
                </label>

                {/* Action Button */}
                <motion.button
                    whileTap={isChecked ? { scale: 0.95 } : {}}
                    whileHover={isChecked ? { scale: 1.02 } : {}}
                    onClick={isChecked ? onConsentGranted : undefined}
                    disabled={!isChecked}
                    className={`w-full max-w-sm h-12 rounded-xl font-medium tracking-wide transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-900 focus-visible:ring-indigo-500 flex items-center justify-center ${isChecked
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_30px_rgba(99,102,241,0.6)] cursor-pointer'
                        : 'bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700/50'
                        }`}
                >
                    Enable COS
                </motion.button>
            </div>
        </motion.div>
    );
};

export default ConsentScreen;
