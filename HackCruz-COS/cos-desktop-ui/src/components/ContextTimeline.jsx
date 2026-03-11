import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export default function ContextTimeline() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/timeline')
      .then(res => res.json())
      .then(data => {
        setEvents(data.timeline || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const getSourceIcon = (url) => {
    if (url.startsWith('os://screen')) return '📸';
    if (url.startsWith('os://')) return '🖥️';
    return '🌐';
  };

  const getSourceColor = (url) => {
    if (url.startsWith('os://screen')) return 'from-emerald-500/20 to-emerald-900/20 border-emerald-500/30';
    if (url.startsWith('os://')) return 'from-purple-500/20 to-purple-900/20 border-purple-500/30';
    return 'from-cos-accent1/20 to-cos-accent2/20 border-cos-accent1/30';
  };

  if (loading) {
    return <div className="p-12 text-cos-textMuted animate-pulse">Syncing semantic memory...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-8">
      <div className="mb-12 border-b border-white/5 pb-6">
        <h2 className="text-2xl font-semibold tracking-tight">Context Timeline</h2>
        <p className="text-cos-textMuted text-sm mt-1">Your chronological semantic memory record</p>
      </div>

      <div className="relative pl-6">
        {/* Vertical Line */}
        <div className="absolute top-0 bottom-0 left-6 w-px bg-gradient-to-b from-cos-accent1 via-cos-accent2 to-transparent" />

        {events.length === 0 ? (
          <div className="text-cos-textMuted text-sm pl-8">No context captured yet.</div>
        ) : (
          events.map((evt, idx) => (
            <motion.div
              key={evt.id || idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="relative pl-8 mb-8"
            >
              {/* Timeline Dot */}
              <div className="absolute left-[-5px] top-6 w-3 h-3 rounded-full bg-cos-bg border-2 border-cos-accent1 ring-4 ring-cos-bg shadow-[0_0_12px_rgba(110,124,255,0.6)]" />

              <div className={`p-6 rounded-2xl bg-gradient-to-br ${getSourceColor(evt.url)} backdrop-blur-xl border hover:-translate-y-1 transition-transform duration-300 shadow-xl`}>
                <div className="flex justify-between items-start mb-3">
                  <div className="text-xs font-semibold text-white/50 bg-black/20 px-3 py-1 rounded-full uppercase tracking-wider backdrop-blur-md">
                    {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div className="text-sm text-cos-textMuted flex items-center gap-2">
                    {getSourceIcon(evt.url)}
                    {evt.url.replace('os://', '').substring(0, 30)}
                  </div>
                </div>
                
                <h3 className="text-lg font-medium text-white mb-2 leading-tight">
                  {evt.title}
                </h3>
                
                <p className="text-sm text-cos-textMuted line-clamp-3 leading-relaxed">
                  {evt.summary || 'No text content available.'}
                </p>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
