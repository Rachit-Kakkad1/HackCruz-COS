import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, ExternalLink, Activity, Target } from 'lucide-react';

export default function CognitiveGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const containerRef = useRef(null);
  const fgRef = useRef();

  const fetchGraph = useCallback(() => {
    fetch('http://localhost:8000/graph')
      .then(res => res.json())
      .then(data => {
        setGraphData({
          nodes: data.nodes.map(n => ({ ...n, val: 5 + (n.count || 1) })),
          links: (data.edges || []).map(e => ({ source: e.source, target: e.target, value: e.weight }))
        });
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetchGraph();
    
    // Establishing Live Thinking Map (WebSocket)
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('COS Live Thinking Map connected');
      setWsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'graph_update') {
         setGraphData({
          nodes: data.nodes.map(n => ({ ...n, val: 5 + (n.count || 1) })),
          links: (data.edges || []).map(e => ({ source: e.source, target: e.target, value: e.weight }))
        });
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
    };

    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    
    window.addEventListener('resize', updateDimensions);
    updateDimensions();

    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, [fetchGraph]);

  const handleResume = async (contextId) => {
    try {
      const res = await fetch(`http://localhost:8000/resume/${contextId}`, {
        method: 'POST'
      });
      const data = await res.json();
      console.log('Resume action result:', data);
      if (data.status === 'launched') {
        // Option to show a toast here
      }
    } catch (err) {
      console.error('Failed to resume context:', err);
    }
  };

  const handleNodeClick = useCallback(node => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 800);
      fgRef.current.zoom(2, 800);
    }
  }, [fgRef]);

  // Premium category-based color palette
  const getCategoryColor = (category) => {
    switch(category) {
      case 'Coding': return '#3b82f6';   // Blue
      case 'Writing': return '#10b981';  // Emerald
      case 'Research': return '#a855f7'; // Purple
      case 'Browsing': return '#f59e0b'; // Amber
      default: return '#6E7CFF';         // Default COS Blue
    }
  };

  return (
    <div className="relative w-full h-full" ref={containerRef}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={graphData}
        nodeRelSize={6}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={d => d.value * 0.01}
        linkColor={() => 'rgba(255, 255, 255, 0.08)'}
        onNodeClick={handleNodeClick}
        backgroundColor="transparent"
        nodeCanvasObject={(node, ctx, globalScale) => {
          const color = getCategoryColor(node.category);
          const label = node.label;
          const fontSize = 12 / globalScale;
          
          // Draw Glow
          ctx.beginPath();
          ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
          ctx.fillStyle = color + '22';
          ctx.fill();

          // Draw Core
          ctx.beginPath();
          ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false);
          ctx.fillStyle = color;
          ctx.fill();
          
          // Labels only if zoomed in enough
          if (globalScale > 0.8) {
            ctx.font = `${fontSize}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#E5E7EB';
            ctx.fillText(label, node.x, node.y + 14);
          }
        }}
      />

      {/* Modern Task Insight Panel */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div 
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 40 }}
            className="absolute top-8 right-8 w-[360px] max-h-[85vh] bg-cos-surface/60 backdrop-blur-3xl border border-white/10 rounded-3xl p-6 shadow-[0_32px_64px_rgba(0,0,0,0.5)] z-10 overflow-hidden flex flex-col"
          >
            <button 
              onClick={() => setSelectedNode(null)}
              className="absolute top-5 right-5 w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/50 hover:text-white transition-colors"
            >
              ✕
            </button>
            
            <div className="flex items-center gap-2 mb-6">
               <div className="px-2 py-1 rounded bg-white/5 border border-white/5 text-[10px] uppercase font-bold tracking-widest text-cos-accent1">
                Cognitive Task
              </div>
              <div className="w-1.5 h-1.5 rounded-full bg-cos-accent1 animate-pulse" />
            </div>
            
            <h3 className="text-xl font-bold text-white mb-2 leading-tight pr-8">
              {selectedNode.label}
            </h3>
            
            <div className="flex items-center gap-4 mb-6 text-cos-textMuted">
              <div className="flex items-center gap-1.5 text-xs">
                <Clock size={14} />
                {new Date(selectedNode.last_active).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
              <div className="flex items-center gap-1.5 text-xs">
                <Target size={14} />
                {selectedNode.category}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-4 mb-6">
              <p className="text-sm text-cos-textMuted leading-relaxed bg-white/5 p-4 rounded-2xl border border-white/5">
                {selectedNode.summary}
              </p>

              <div>
                <h4 className="text-[11px] uppercase font-bold tracking-wider text-white/30 mb-3 flex items-center gap-2">
                  <Activity size={12} /> Related Contexts
                </h4>
                <div className="space-y-2">
                  {selectedNode.contexts.map((ctx, i) => (
                    <div key={i} className="p-3 bg-white/5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors group">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-medium text-white line-clamp-1">{ctx.title}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-cos-textMuted">
                         <span>{new Date(ctx.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
                         <span className="opacity-30">•</span>
                         <span className="truncate max-w-[150px]">{new URL(ctx.url).hostname}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-white/5">
              <button 
                onClick={() => handleResume(selectedNode.contexts[0].id)}
                className="w-full py-3 bg-white text-black font-bold rounded-xl flex items-center justify-center gap-2 hover:bg-emerald-400 active:scale-[0.98] transition-all"
              >
                Resume Thinking
                <ExternalLink size={16} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Legend */}
      <div className="absolute bottom-8 left-8 p-4 bg-cos-surface/40 backdrop-blur-xl border border-white/5 rounded-2xl flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-[10px] uppercase font-bold tracking-widest text-white/70">
            {wsConnected ? 'Live Thinking Map' : 'Reconnecting...'}
          </span>
        </div>
        
        <div className="flex items-center gap-3 text-xs text-cos-textMuted">
          <div className="w-2 h-2 rounded-full bg-[#3b82f6]" /> Coding
          <div className="w-2 h-2 rounded-full bg-[#a855f7]" /> Research
          <div className="w-2 h-2 rounded-full bg-[#10b981]" /> Writing
          <div className="w-2 h-2 rounded-full bg-[#f59e0b]" /> Browsing
        </div>
      </div>
    </div>
  );
}
