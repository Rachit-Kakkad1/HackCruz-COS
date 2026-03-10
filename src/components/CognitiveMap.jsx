import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion, AnimatePresence } from 'framer-motion';
import { ExternalLink, X, Clock, Globe } from 'lucide-react';
import CognitiveMapNode from './CognitiveMapNode';

// ─── DATA FETCHING ───────────────────────────────────────────────────────────
// Tries the real backend first. Falls back to mock data when backend is offline.
const API_BASE = "http://localhost:8000";
const USER_ID = "550e8400-e29b-41d4-a716-446655440000";

const MOCK_DATA = {
    nodes: [
        { id: '1', title: 'AWS Lambda IAM Documentation', domain: 'docs.aws.amazon.com', timestamp: '10:21', url: 'https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html', cluster: 'aws-auth' },
        { id: '2', title: 'StackOverflow: Lambda 403 Error', domain: 'stackoverflow.com', timestamp: '10:24', url: 'https://stackoverflow.com/questions/lambda-403', cluster: 'aws-auth' },
        { id: '3', title: 'GitHub Issue: IAM Policy Bug', domain: 'github.com', timestamp: '10:30', url: 'https://github.com/aws/aws-cdk/issues/12345', cluster: 'aws-auth' },
        { id: '4', title: 'React Flow Documentation', domain: 'reactflow.dev', timestamp: '11:05', url: 'https://reactflow.dev/docs/getting-started/', cluster: 'ui-research' },
        { id: '5', title: 'D3.js Force Layout Examples', domain: 'd3js.org', timestamp: '11:12', url: 'https://observablehq.com/@d3/force-directed-graph', cluster: 'ui-research' },
        { id: '6', title: 'Framer Motion API Reference', domain: 'framer.com', timestamp: '11:18', url: 'https://www.framer.com/motion/', cluster: 'ui-research' },
        { id: '7', title: 'Tailwind CSS Dark Mode Guide', domain: 'tailwindcss.com', timestamp: '11:25', url: 'https://tailwindcss.com/docs/dark-mode', cluster: 'ui-research' },
        { id: '8', title: 'OpenAI API — Embeddings', domain: 'platform.openai.com', timestamp: '12:01', url: 'https://platform.openai.com/docs/guides/embeddings', cluster: 'ai-pipeline' },
        { id: '9', title: 'Pinecone Vector DB Quickstart', domain: 'docs.pinecone.io', timestamp: '12:08', url: 'https://docs.pinecone.io/docs/quickstart', cluster: 'ai-pipeline' },
        { id: '10', title: 'LangChain RAG Tutorial', domain: 'python.langchain.com', timestamp: '12:15', url: 'https://python.langchain.com/docs/tutorials/rag', cluster: 'ai-pipeline' },
        { id: '11', title: 'Chrome Extensions Manifest V3', domain: 'developer.chrome.com', timestamp: '12:30', url: 'https://developer.chrome.com/docs/extensions/mv3/', cluster: null },
        { id: '12', title: 'MDN: Service Workers API', domain: 'developer.mozilla.org', timestamp: '12:35', url: 'https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API', cluster: null },
    ],
    edges: [
        { source: '1', target: '2', type: 'temporal' },
        { source: '2', target: '3', type: 'semantic' },
        { source: '1', target: '3', type: 'semantic' },
        { source: '4', target: '5', type: 'semantic' },
        { source: '5', target: '6', type: 'temporal' },
        { source: '6', target: '7', type: 'semantic' },
        { source: '4', target: '7', type: 'cluster' },
        { source: '8', target: '9', type: 'semantic' },
        { source: '9', target: '10', type: 'temporal' },
        { source: '8', target: '10', type: 'cluster' },
        { source: '3', target: '8', type: 'temporal' },
        { source: '11', target: '12', type: 'semantic' },
    ],
    clusters: [
        { id: 'aws-auth', label: 'Debugging AWS Lambda Auth Error', nodeIds: ['1', '2', '3'] },
        { id: 'ui-research', label: 'Graph Visualization Research', nodeIds: ['4', '5', '6', '7'] },
        { id: 'ai-pipeline', label: 'Building RAG Pipeline', nodeIds: ['8', '9', '10'] },
    ],
};

const fetchGraphData = async () => {
    // Try the real backend first
    try {
        const res = await fetch(`${API_BASE}/api/v1/context/map?userId=${USER_ID}&limit=100`);
        if (res.ok) {
            const data = await res.json();
            // Only use real data if we actually have nodes
            if (data.nodes && data.nodes.length > 0) return data;
        }
    } catch {
        // Backend unreachable — use mock data
    }
    return MOCK_DATA;
};

// ─── EDGE STYLE MAP ──────────────────────────────────────────────────────────
const edgeStyleMap = {
    semantic: {
        style: { stroke: '#6366f1', strokeWidth: 2 },
        type: 'default', // curved bezier
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 12, height: 12 },
    },
    temporal: {
        style: { stroke: '#52525b', strokeWidth: 1.5 },
        type: 'straight',
        animated: false,
    },
    cluster: {
        style: { stroke: '#a855f7', strokeWidth: 1.5, strokeDasharray: '6 4' },
        type: 'default',
        animated: false,
    },
};

// ─── LAYOUT HELPERS ──────────────────────────────────────────────────────────
// Simple force-directed-ish layout: arrange nodes in cluster groups
const computeLayout = (apiNodes, clusters) => {
    const clusterMap = {};
    clusters.forEach((c, i) => {
        c.nodeIds.forEach(nid => { clusterMap[nid] = { clusterId: c.id, index: i }; });
    });

    // Cluster center positions — spread horizontally
    const clusterCenters = {};
    const clusterSpacing = 320;
    clusters.forEach((c, i) => {
        clusterCenters[c.id] = {
            x: 80 + (i % 3) * clusterSpacing,
            y: 80 + Math.floor(i / 3) * 300,
        };
    });

    let unclusteredX = 80;
    const unclusteredY = (clusters.length > 0 ? Math.ceil(clusters.length / 3) : 0) * 300 + 120;

    // Track per-cluster node count for offset
    const clusterNodeCount = {};

    return apiNodes.slice(0, 100).map((node) => {
        const cm = clusterMap[node.id];
        let x, y;

        if (cm && clusterCenters[cm.clusterId]) {
            const center = clusterCenters[cm.clusterId];
            clusterNodeCount[cm.clusterId] = (clusterNodeCount[cm.clusterId] || 0);
            const idx = clusterNodeCount[cm.clusterId];
            // Arrange in a small grid within the cluster
            x = center.x + (idx % 2) * 200;
            y = center.y + Math.floor(idx / 2) * 100;
            clusterNodeCount[cm.clusterId]++;
        } else {
            x = unclusteredX;
            y = unclusteredY;
            unclusteredX += 220;
        }

        return {
            id: node.id,
            type: 'cognitiveNode',
            position: { x, y },
            data: { ...node },
        };
    });
};

const computeEdges = (apiEdges) => {
    return apiEdges.map((edge, i) => {
        const styleConfig = edgeStyleMap[edge.type] || edgeStyleMap.temporal;
        return {
            id: `e-${edge.source}-${edge.target}-${i}`,
            source: edge.source,
            target: edge.target,
            type: styleConfig.type,
            animated: styleConfig.animated,
            style: styleConfig.style,
            markerEnd: styleConfig.markerEnd,
        };
    });
};

// ─── CLUSTER HALO COMPONENT ─────────────────────────────────────────────────
const ClusterHalo = ({ cluster, nodes }) => {
    const clusterNodes = nodes.filter(n => cluster.nodeIds.includes(n.id));
    if (clusterNodes.length === 0) return null;

    const xs = clusterNodes.map(n => n.position.x);
    const ys = clusterNodes.map(n => n.position.y);
    const padding = 40;
    const nodeWidth = 210;
    const nodeHeight = 50;

    const left = Math.min(...xs) - padding;
    const top = Math.min(...ys) - padding - 20; // extra for label
    const right = Math.max(...xs) + nodeWidth + padding;
    const bottom = Math.max(...ys) + nodeHeight + padding;

    const colorMap = {
        'aws-auth': 'rgba(99, 102, 241, 0.06)',
        'ui-research': 'rgba(168, 85, 247, 0.06)',
        'ai-pipeline': 'rgba(34, 197, 94, 0.06)',
    };
    const borderColorMap = {
        'aws-auth': 'rgba(99, 102, 241, 0.15)',
        'ui-research': 'rgba(168, 85, 247, 0.15)',
        'ai-pipeline': 'rgba(34, 197, 94, 0.15)',
    };

    return (
        <div
            className="absolute rounded-2xl pointer-events-none"
            style={{
                left, top, width: right - left, height: bottom - top,
                background: colorMap[cluster.id] || 'rgba(99, 102, 241, 0.04)',
                border: `1px solid ${borderColorMap[cluster.id] || 'rgba(99, 102, 241, 0.1)'}`,
            }}
        >
            <span className="absolute -top-3 left-4 text-[9px] font-semibold text-zinc-400 bg-zinc-950/80 px-2 py-0.5 rounded-full uppercase tracking-wider">
                {cluster.label}
            </span>
        </div>
    );
};

// ─── DETAIL POPUP ────────────────────────────────────────────────────────────
const NodeDetailPopup = ({ node, onClose }) => {
    if (!node) return null;

    const handleOpenTab = () => {
        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
            chrome.runtime.sendMessage({ action: 'OPEN_TAB', url: node.url });
        } else {
            // Dev fallback — open in new window tab
            window.open(node.url, '_blank');
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-[320px] glass-card rounded-xl p-4 border border-indigo-500/20 shadow-[0_8px_32px_rgba(99,102,241,0.15)]"
        >
            {/* Close button */}
            <button
                onClick={onClose}
                className="absolute top-2 right-2 p-1 text-zinc-500 hover:text-zinc-300 transition-colors"
            >
                <X className="w-3.5 h-3.5" />
            </button>

            <div className="flex items-start gap-3">
                <div className="w-8 h-8 shrink-0 flex items-center justify-center rounded-lg bg-zinc-900 border border-white/5 overflow-hidden">
                    <img
                        src={`https://www.google.com/s2/favicons?domain=${node.domain}&sz=64`}
                        alt=""
                        className="w-4 h-4 object-contain"
                    />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-[13px] font-semibold text-zinc-200 leading-snug mb-1">
                        {node.title}
                    </h3>
                    <div className="flex items-center gap-3 text-[10px] text-zinc-500 mb-3">
                        <span className="flex items-center gap-1">
                            <Globe className="w-3 h-3" /> {node.domain}
                        </span>
                        <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {node.timestamp}
                        </span>
                    </div>
                </div>
            </div>

            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleOpenTab}
                className="w-full bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 text-[11px] font-semibold py-2 rounded-lg flex items-center justify-center gap-1.5 border border-indigo-500/20 transition-colors"
            >
                <ExternalLink className="w-3.5 h-3.5" />
                Open Tab
            </motion.button>
        </motion.div>
    );
};

// ─── MAIN COMPONENT ─────────────────────────────────────────────────────────
const nodeTypes = { cognitiveNode: CognitiveMapNode };

const CognitiveMap = () => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [clusters, setClusters] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch graph data on mount
    useEffect(() => {
        const loadData = async () => {
            setIsLoading(true);
            try {
                const data = await fetchGraphData();
                const layoutNodes = computeLayout(data.nodes, data.clusters || []);
                const layoutEdges = computeEdges(data.edges);
                setNodes(layoutNodes);
                setEdges(layoutEdges);
                setClusters(data.clusters || []);
            } catch (err) {
                console.error('COS: Failed to load cognitive map data', err);
            } finally {
                setIsLoading(false);
            }
        };
        loadData();
    }, []);

    // Handle node click to show detail popup
    const onNodeClick = useCallback((event, node) => {
        setSelectedNode(node.data);
    }, []);

    // Handle pane click to dismiss popup
    const onPaneClick = useCallback(() => {
        setSelectedNode(null);
    }, []);

    // Loading state
    if (isLoading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                    <p className="text-[11px] text-zinc-500 tracking-wide">Mapping your cognition...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 relative overflow-hidden cognitive-map-container">
            {/* Cluster halos rendered as absolute overlays inside React Flow viewport */}
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.3 }}
                minZoom={0.3}
                maxZoom={2}
                proOptions={{ hideAttribution: true }}
                className="cognitive-map-flow"
            >
                <Background color="#27272a" gap={24} size={1} />
                <Controls
                    showInteractive={false}
                    className="cognitive-map-controls"
                />
                <MiniMap
                    nodeColor="#6366f1"
                    maskColor="rgba(9, 9, 11, 0.85)"
                    className="cognitive-map-minimap"
                    pannable
                    zoomable
                />
            </ReactFlow>

            {/* Node Detail Popup */}
            <AnimatePresence>
                {selectedNode && (
                    <NodeDetailPopup
                        node={selectedNode}
                        onClose={() => setSelectedNode(null)}
                    />
                )}
            </AnimatePresence>

            {/* Edge Legend */}
            <div className="absolute top-3 left-3 z-40 glass-card rounded-lg px-3 py-2 border border-white/5">
                <div className="flex items-center gap-4 text-[9px] text-zinc-400">
                    <span className="flex items-center gap-1.5">
                        <span className="w-4 h-0.5 bg-indigo-500 rounded-full" /> Semantic
                    </span>
                    <span className="flex items-center gap-1.5">
                        <span className="w-4 h-0.5 bg-zinc-600 rounded-full" /> Temporal
                    </span>
                    <span className="flex items-center gap-1.5">
                        <span className="w-4 h-px border-t border-dashed border-purple-500" style={{ width: '16px' }} /> Cluster
                    </span>
                </div>
            </div>
        </div>
    );
};

export default CognitiveMap;
