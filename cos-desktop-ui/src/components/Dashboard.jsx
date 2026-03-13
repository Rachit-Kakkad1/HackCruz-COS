import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Network, Mic, Clock, Brain, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ContextTimeline from './ContextTimeline';
import CognitiveGraph from './CognitiveGraph';
import FocusRadar from './FocusRadar';
import TimelineSlider from './TimelineSlider';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('graph');
  const [health, setHealth] = useState(false);
  const [focusSuggestion, setFocusSuggestion] = useState(null);
  
  // Time Travel State
  const [isTimeTraveling, setIsTimeTraveling] = useState(false);
  const [scrubTime, setScrubTime] = useState(Math.floor(Date.now() / 1000));
  const [timeRange, setTimeRange] = useState({ min: 0, max: 0 });
  const [historicalGraph, setHistoricalGraph] = useState(null);

  const fetchTimeRange = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/time_range');
      const data = await res.json();
      setTimeRange(data);
      if (!isTimeTraveling) {
        setScrubTime(data.max);
      }
    } catch (err) {
      console.error('Failed to fetch time range:', err);
    }
  }, [isTimeTraveling]);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setHealth(data.status === 'ok'))
      .catch(() => setHealth(false));
      
    fetchTimeRange();

    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'focus_radar_suggestion') {
        setFocusSuggestion(data);
      }
      if (data.type === 'graph_update' && !isTimeTraveling) {
        // Refresh time range on new live data
        fetchTimeRange();
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
  }, [fetchTimeRange, isTimeTraveling]);

  const handleScrub = async (time) => {
    setScrubTime(time);
    const isNow = time >= timeRange.max;
    setIsTimeTraveling(!isNow);

    if (!isNow) {
      try {
        const res = await fetch(`http://localhost:8000/contexts_at_time?timestamp=${time}`);
        const data = await res.json();
        setHistoricalGraph(data);
      } catch (err) {
        console.error('Temporal query failed:', err);
      }
    } else {
      setHistoricalGraph(null);
    }
  };

  const handleResume = async (contextId) => {
    try {
      await fetch(`http://localhost:8000/resume/${contextId}`, { method: 'POST' });
    } catch (err) {
      console.error('Proactive resume failed:', err);
    }
  };

  return (
    <div className="flex h-screen bg-[#050505] text-white font-sans selection:bg-emerald-500/30">
      
      {/* Sidebar Layout */}
      <aside className="w-72 border-r border-emerald-500/10 bg-black/40 backdrop-blur-3xl flex flex-col items-center py-10 z-20">
        
        {/* Brand */}
        <div className="flex items-center gap-4 w-full px-8 mb-16">
          <motion.div 
            whileHover={{ scale: 1.05, rotate: 5 }}
            className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-blue-600 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.3)]"
          >
            <Brain size={24} className="text-white" />
          </motion.div>
          <div>
            <h1 className="font-bold tracking-tight text-xl bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">COS</h1>
            <p className="text-[10px] text-emerald-400/70 uppercase tracking-[0.2em] font-bold mt-0.5">Neural Layer</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="w-full px-6 flex flex-col gap-3">
          <button 
            onClick={() => setActiveTab('graph')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 ${
              activeTab === 'graph' 
                ? 'bg-emerald-500/10 text-emerald-400 shadow-[inset_0_0_20px_rgba(16,185,129,0.05)] border border-emerald-500/20' 
                : 'text-gray-500 hover:bg-white/5 hover:text-gray-300 border border-transparent'
            }`}
          >
            <Network size={20} />
            <span className="font-semibold text-sm">Thinking Map</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('timeline')}
            className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 ${
              activeTab === 'timeline' 
                ? 'bg-emerald-500/10 text-emerald-400 shadow-[inset_0_0_20px_rgba(16,185,129,0.05)] border border-emerald-500/20' 
                : 'text-gray-500 hover:bg-white/5 hover:text-gray-300 border border-transparent'
            }`}
          >
            <Clock size={20} />
            <span className="font-semibold text-sm">Chronology</span>
          </button>
        </nav>

        <div className="mt-auto w-full px-8 pb-4">
          <div className="p-5 flex flex-col gap-4 bg-emerald-500/5 rounded-3xl border border-emerald-500/10">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-widest font-bold text-gray-500">Core Engine</span>
              <div className={`w-2 h-2 rounded-full ${health ? 'bg-emerald-400 shadow-[0_0_12px_#10b981]' : 'bg-red-500'} animate-pulse`} />
            </div>
            
            <div className="flex items-center gap-3">
              <Mic size={16} className="text-blue-500" />
              <span className="text-[11px] font-bold text-gray-400 italic">Listening for Ctrl+Alt+Space</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 relative overflow-hidden bg-black">
        {/* Background Ambient Glow */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-emerald-600/10 blur-[120px] rounded-full -mr-64 -mt-64 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-blue-600/5 blur-[100px] rounded-full -ml-32 -mb-32 pointer-events-none" />

        <AnimatePresence mode="wait">
          {activeTab === 'graph' ? (
            <motion.div 
              key="graph"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.02 }}
              className="absolute inset-0"
            >
              <CognitiveGraph 
                isHistorical={isTimeTraveling} 
                historicalData={historicalGraph}
                onRestore={handleResume}
              />
            </motion.div>
          ) : (
            <motion.div 
              key="timeline"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="absolute inset-0 overflow-y-auto px-12 py-16"
            >
              <ContextTimeline />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Global Time Travel Controls */}
        <TimelineSlider 
          min={timeRange.min} 
          max={timeRange.max} 
          value={scrubTime} 
          onChange={handleScrub} 
        />
      </main>

      <FocusRadar 
        suggestion={focusSuggestion} 
        onResume={handleResume} 
        onDismiss={() => setFocusSuggestion(null)} 
      />
    </div>
  );
}
