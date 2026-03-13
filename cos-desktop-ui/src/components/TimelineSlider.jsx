import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Rewind, Play } from 'lucide-react';

export default function TimelineSlider({ min, max, value, onChange }) {
  const formatTime = (ts) => {
    if (!ts) return "---";
    return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const isOldest = value === min;
  const isLatest = value === max;

  return (
    <motion.div 
      initial={{ y: 50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-3/4 max-w-2xl bg-black/60 backdrop-blur-xl border border-emerald-500/30 rounded-full px-8 py-4 flex items-center gap-6 shadow-2xl z-50"
    >
      <div className="flex flex-col items-center min-w-[100px]">
        <span className="text-xs text-emerald-400 font-mono uppercase tracking-widest mb-1 flex items-center gap-1">
          <Clock size={12} /> {isLatest ? "Live Thinking" : "Memory Recall"}
        </span>
        <span className="text-lg font-bold text-white tabular-nums drop-shadow-glow">
          {formatTime(value)}
        </span>
      </div>

      <div className="flex-1 flex items-center gap-4 group">
        <Rewind size={20} className={`cursor-pointer transition-colors ${isOldest ? 'text-gray-600' : 'text-emerald-500 hover:text-emerald-400'}`} onClick={() => onChange(min)} />
        
        <div className="relative flex-1 h-2 flex items-center">
          <input
            type="range"
            min={min}
            max={max}
            step="1"
            value={value}
            onChange={(e) => onChange(parseInt(e.target.value))}
            className="w-full h-1 bg-gray-800 rounded-full appearance-none cursor-pointer accent-emerald-500 hover:accent-emerald-400 focus:outline-none transition-all"
            style={{
                background: `linear-gradient(to right, #10b981 0%, #10b981 ${((value - min) / (max - min)) * 100}%, #1f2937 ${((value - min) / (max - min)) * 100}%, #1f2937 100%)`
            }}
          />
          <div 
            className="absolute -top-1 pointer-events-none" 
            style={{ left: `${((value - min) / (max - min)) * 100}%` }}
          >
             <div className="w-4 h-4 bg-emerald-400 rounded-full shadow-[0_0_15px_#10b981] animate-pulse" />
          </div>
        </div>

        <Play size={20} className={`cursor-pointer transition-colors ${isLatest ? 'text-gray-600' : 'text-emerald-500 hover:text-emerald-400'}`} onClick={() => onChange(max)} />
      </div>

      <style jsx>{`
        input[type='range']::-webkit-slider-thumb {
          appearance: none;
          width: 0;
          height: 0;
        }
        .drop-shadow-glow {
          filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.5));
        }
      `}</style>
    </motion.div>
  );
}
