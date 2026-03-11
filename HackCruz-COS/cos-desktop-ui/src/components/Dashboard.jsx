import React, { useState, useEffect } from 'react';
import { Activity, Network, Mic, Clock, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ContextTimeline from './ContextTimeline';
import CognitiveGraph from './CognitiveGraph';
import FocusRadar from './FocusRadar';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('graph');
  const [health, setHealth] = useState(false);

  const [focusSuggestion, setFocusSuggestion] = useState(null);

  useEffect(() => {
    // Check backend health
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setHealth(data.status === 'ok'))
      .catch(() => setHealth(false));
      
    // WebSocket for Focus Radar suggestions
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'focus_radar_suggestion') {
        console.log('Focus Radar Suggestion:', data);
        setFocusSuggestion(data);
      }
    };

    const interval = setInterval(() => {
      fetch('http://localhost:8000/health')
        .then(res => res.json())
        .then(data => setHealth(data.status === 'ok'))
        .catch(() => setHealth(false));
    }, 10000);

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, []);

  const handleResume = async (contextId) => {
    try {
      await fetch(`http://localhost:8000/resume/${contextId}`, { method: 'POST' });
    } catch (err) {
      console.error('Proactive resume failed:', err);
    }
  };

  return (
    <div className="flex h-screen bg-cos-bg text-cos-text font-sans">
      
      {/* Sidebar Layout */}
      <aside className="w-64 border-r border-white/5 bg-cos-surface/50 backdrop-blur-xl flex flex-col items-center py-8 z-20">
        
        {/* Brand */}
        <div className="flex items-center gap-3 w-full px-6 mb-12">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cos-accent1 to-cos-accent2 flex items-center justify-center shadow-[0_0_20px_rgba(110,124,255,0.3)]">
            <Brain size={20} className="text-white" />
          </div>
          <div>
            <h1 className="font-semibold tracking-tight text-white">Cognitive OS</h1>
            <p className="text-[11px] text-cos-textMuted uppercase tracking-wider font-medium mt-0.5">Control Center</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="w-full px-4 flex flex-col gap-2">
          <button 
            onClick={() => setActiveTab('graph')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'graph' 
                ? 'bg-white/10 text-white shadow-sm ring-1 ring-white/5' 
                : 'text-cos-textMuted hover:bg-white/5 hover:text-white'
            }`}
          >
            <Network size={18} />
            <span className="font-medium text-sm">Cognitive Graph</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('timeline')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'timeline' 
                ? 'bg-white/10 text-white shadow-sm ring-1 ring-white/5' 
                : 'text-cos-textMuted hover:bg-white/5 hover:text-white'
            }`}
          >
            <Clock size={18} />
            <span className="font-medium text-sm">Context Timeline</span>
          </button>
        </nav>

        <div className="mt-auto w-full px-6">
          {/* Status Indicator */}
          <div className="flex items-center gap-2 px-4 py-3 bg-cos-surface rounded-xl border border-white/5">
            <div className={`w-2 h-2 rounded-full ${health ? 'bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.6)] animate-pulse' : 'bg-red-500'}`} />
            <span className="text-xs font-medium text-cos-textMuted">
              {health ? 'Core Online' : 'Core Offline'}
            </span>
          </div>
          
          {/* Voice Indicator */}
          <div className="mt-4 flex items-center gap-2 px-4 py-3 bg-cos-surface rounded-xl border border-white/5">
           <Mic size={14} className="text-cos-accent2" />
           <span className="text-xs text-cos-textMuted">Ctrl+Alt+Space to Speak</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-cos-accent1/10 via-cos-bg to-cos-bg">
        <AnimatePresence mode="wait">
          {activeTab === 'graph' ? (
            <motion.div 
              key="graph"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.02 }}
              transition={{ duration: 0.3 }}
              className="absolute inset-0"
            >
              <CognitiveGraph />
            </motion.div>
          ) : (
            <motion.div 
              key="timeline"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="absolute inset-0 overflow-y-auto"
            >
              <ContextTimeline />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <FocusRadar 
        suggestion={focusSuggestion} 
        onResume={handleResume} 
        onDismiss={() => setFocusSuggestion(null)} 
      />
    </div>
  );
}
