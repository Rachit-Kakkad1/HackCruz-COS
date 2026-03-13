import React, { useState, useEffect, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, ExternalLink, Activity, Target } from 'lucide-react';

export default function CognitiveGraph({ isHistorical, historicalData, onRestore }) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const containerRef = useRef(null);
  const fgRef = useRef();

  const processGraphData = useCallback((data) => {
    return {
      nodes: data.nodes.map(n => ({ 
        ...n, 
        val: isHistorical ? 12 : (8 + (n.count || 1)), // Larger for Task Nodes
        label: n.label || n.title,
        category: n.category || 'Activity'
      })),
      links: (data.edges || data.links || []).map(e => ({ 
        source: e.source, 
        target: e.target, 
        value: e.weight || 1 
      })),
      is_windowed: data.is_windowed,
      window_start: data.window_start
    };
  }, [isHistorical]);

  const fetchGraph = useCallback(() => {
    if (isHistorical && historicalData) {
      setGraphData(processGraphData(historicalData));
      return;
    }

    fetch('http://localhost:8000/graph')
      .then(res => res.json())
      .then(data => {
        setGraphData(processGraphData(data));
      })
      .catch(console.error);
  }, [isHistorical, historicalData, processGraphData]);

  useEffect(() => {
    if (isHistorical) {
      if (historicalData) {
        setGraphData(processGraphData(historicalData));
      }
    } else {
      fetchGraph();
      
      const ws = new WebSocket('ws://localhost:8000/ws');
      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'graph_update') {
          setGraphData(processGraphData(data));
        }
      };
      ws.onclose = () => setWsConnected(false);
      return () => ws.close();
    }
  }, [isHistorical, historicalData, fetchGraph, processGraphData]);

  useEffect(() => {
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
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const handleNodeClick = useCallback(node => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 800);
      fgRef.current.zoom(2.5, 800);
    }
  }, [fgRef]);

  const getCategoryColor = (category) => {
    switch(category) {
      case 'Coding': return '#3b82f6';
      case 'Writing': return '#10b981';
      case 'Research': return '#a855f7';
      case 'Browsing': return '#f59e0b';
      default: return '#10b981';
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
        linkDirectionalParticles={isHistorical ? 0 : 2}
        linkDirectionalParticleSpeed={d => (d.value || 1) * 0.01}
        linkColor={() => isHistorical ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.08)'}
        onNodeClick={handleNodeClick}
        backgroundColor="transparent"
        cooldownTicks={100}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const color = getCategoryColor(node.category);
          const label = node.label;
          const fontSize = 12 / globalScale;
          
          ctx.beginPath();
          ctx.arc(node.x, node.y, isHistorical ? 6 : 8, 0, 2 * Math.PI, false);
          ctx.fillStyle = color + '22';
          ctx.fill();

          ctx.beginPath();
          ctx.arc(node.x, node.y, isHistorical ? 4 : 5, 0, 2 * Math.PI, false);
          ctx.fillStyle = color;
          ctx.fill();
          
          if (globalScale > 1.2) {
            ctx.font = `${fontSize}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = isHistorical ? '#10b981' : '#E5E7EB';
            ctx.fillText(label, node.x, node.y + 14);
          }
        }}
      />

      <div className="absolute top-8 left-8 flex flex-col gap-3 pointer-events-none z-10">
        {isHistorical && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 backdrop-blur-md border border-emerald-500/20 rounded-2xl"
          >
            <Clock size={14} className="text-emerald-500" />
            <span className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.1em]">
              24h Context Window
            </span>
          </motion.div>
        )}
      </div>

      <AnimatePresence>
        {selectedNode && (
          <motion.div 
            initial={{ opacity: 0, x: 50, filter: 'blur(10px)' }}
            animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, x: 50, filter: 'blur(10px)' }}
            className="absolute top-8 right-8 w-[380px] bg-black/40 backdrop-blur-3xl border border-emerald-500/20 rounded-[2.5rem] p-8 shadow-[0_40px_80px_rgba(0,0,0,0.7)] z-10 flex flex-col"
          >
            <button 
              onClick={() => setSelectedNode(null)}
              className="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/50 hover:text-white transition-all"
            >
              ✕
            </button>
            
            <div className="flex items-center gap-3 mb-8">
               <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] uppercase font-black tracking-[0.2em] text-emerald-400">
                {isHistorical ? 'Historical Reflection' : 'Neural Cluster'}
              </div>
              <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#10b981] animate-pulse" />
            </div>
            
            <h3 className="text-2xl font-bold text-white mb-4 leading-tight">
              {selectedNode.label}
            </h3>
            
            <div className="flex items-center gap-6 mb-8 text-gray-400">
              <div className="flex items-center gap-2 text-xs font-bold">
                <Clock size={16} className="text-emerald-500" />
                {new Date(isHistorical ? selectedNode.timestamp * 1000 : selectedNode.last_active).toLocaleString()}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 mb-8">
              <div className="p-6 bg-emerald-500/5 rounded-3xl border border-emerald-500/10 mb-6">
                <p className="text-sm text-gray-300 leading-relaxed italic">
                  "{selectedNode.summary || (isHistorical ? `Context cluster from ${selectedNode.app}` : 'No summary available.')}"
                </p>
              </div>

              {selectedNode.contexts && (
                <div>
                  <h4 className="text-[10px] uppercase font-black tracking-[0.2em] text-gray-500 mb-4 flex items-center gap-2">
                    <Activity size={12} /> Activity Log ({selectedNode.count || selectedNode.contexts.length})
                  </h4>
                  <div className="grid gap-3">
                    {selectedNode.contexts.slice(0, 10).map((ctx, i) => (
                      <div key={i} className="p-4 bg-white/5 rounded-2xl border border-white/5 hover:border-emerald-500/30 transition-all group">
                        <div className="flex justify-between items-start">
                          <span className="text-xs font-bold text-gray-200 line-clamp-1">{ctx.title}</span>
                          <span className="text-[9px] text-emerald-500/60 font-mono">
                            {new Date(ctx.timestamp * 1000).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                          </span>
                        </div>
                        <span className="text-[10px] text-gray-500 mt-1 block truncate">
                          {ctx.url ? new URL(ctx.url).hostname : ctx.app}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <button 
              onClick={() => onRestore(isHistorical ? selectedNode.id : selectedNode.contexts[0].id)}
              className="w-full py-4 bg-emerald-500 text-black font-black uppercase tracking-widest rounded-2xl flex items-center justify-center gap-3 hover:bg-emerald-400 hover:shadow-[0_0_20px_#10b981] active:scale-[0.98] transition-all transform"
            >
              Restore This Moment
              <ExternalLink size={18} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute bottom-10 left-10 p-6 bg-black/40 backdrop-blur-2xl border border-emerald-500/10 rounded-3xl flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${wsConnected || isHistorical ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-red-500'}`} />
          <span className="text-[10px] uppercase font-black tracking-[0.2em] text-gray-400">
            {isHistorical ? 'Time Travel Mode' : (wsConnected ? 'Thinking Live' : 'Disconnected')}
          </span>
        </div>
        
        <div className="flex items-center gap-4 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
          <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-[#3b82f6]" /> Coding</div>
          <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-[#a855f7]" /> Research</div>
          <div className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-[#10b981]" /> Context</div>
        </div>
      </div>
    </div>
  );
}
