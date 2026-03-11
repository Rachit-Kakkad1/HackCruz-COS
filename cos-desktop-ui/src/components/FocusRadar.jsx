import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, X, Play, Target } from 'lucide-react';

export default function FocusRadar({ suggestion, onResume, onDismiss }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (suggestion) {
      setVisible(true);
      // Auto-hide after 15 seconds if no interaction
      const timer = setTimeout(() => setVisible(false), 15000);
      return () => clearTimeout(timer);
    }
  }, [suggestion]);

  if (!suggestion || !visible) return null;

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 w-[400px] z-[100]"
        >
          <div className="relative overflow-hidden bg-cos-surface/60 backdrop-blur-3xl border border-cos-accent1/30 rounded-3xl p-6 shadow-[0_32px_80px_rgba(0,0,0,0.6)] group">
            
            {/* Ambient Pulse Effect */}
            <div className="absolute inset-0 bg-cos-accent1/5 animate-pulse" />
            
            <div className="relative z-10">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-cos-accent1/20 flex items-center justify-center text-cos-accent1">
                    <Zap size={18} fill="currentColor" />
                  </div>
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-widest text-cos-accent1/80">
                      Focus Radar
                    </h4>
                    <div className="flex items-center gap-2 text-[10px] text-white/50">
                      <Target size={10} />
                      Confidence: {Math.round(suggestion.confidence * 100)}%
                    </div>
                  </div>
                </div>
                <button 
                  onClick={() => {
                    setVisible(false);
                    onDismiss?.();
                  }}
                  className="p-1.5 rounded-full hover:bg-white/5 text-white/30 hover:text-white transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="mb-6">
                <p className="text-white/60 text-xs mb-1 font-medium">Likely Next Task:</p>
                <h3 className="text-lg font-bold text-white leading-tight">
                  {suggestion.task}
                </h3>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    onResume(suggestion.context_id);
                    setVisible(false);
                  }}
                  className="flex-1 py-3 bg-cos-accent1 text-cos-background font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-emerald-400 active:scale-[0.98] transition-all shadow-[0_8px_20px_rgba(16,185,129,0.3)]"
                >
                  <Play size={16} fill="currentColor" />
                  Resume Flow
                </button>
                <button
                  onClick={() => {
                    setVisible(false);
                    onDismiss?.();
                  }}
                  className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all border border-white/5"
                >
                  Ignore
                </button>
              </div>
            </div>

            {/* Scanning Line Animation */}
            <motion.div 
              className="absolute left-0 top-0 w-full h-[1px] bg-gradient-to-r from-transparent via-cos-accent1/50 to-transparent"
              animate={{ top: ['0%', '100%', '0%'] }}
              transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
