import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { motion } from 'framer-motion';

/**
 * CognitiveMapNode — Custom React Flow node rendered as a glassmorphic card.
 * Displays favicon, page title, domain, and timestamp.
 * Clicking the node triggers onNodeClick in the parent to show a detail popup.
 */
const CognitiveMapNode = ({ data }) => {
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${data.domain}&sz=64`;

    return (
        <>
            {/* Invisible handles for edges */}
            <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-0 !h-0" />
            <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-0 !h-0" />

            <motion.div
                whileHover={{ scale: 1.06, y: -2 }}
                transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                className="cognitive-map-node group cursor-pointer"
            >
                {/* Hover glow effect */}
                <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-indigo-500/0 via-indigo-500/0 to-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                <div className="flex items-center gap-2.5 relative z-10">
                    {/* Favicon */}
                    <div className="w-7 h-7 shrink-0 flex items-center justify-center rounded-lg bg-zinc-900 border border-white/5 overflow-hidden shadow-sm group-hover:border-indigo-500/30 transition-colors">
                        <img
                            src={faviconUrl}
                            alt=""
                            className="w-4 h-4 object-contain"
                            onError={(e) => { e.target.style.display = 'none'; }}
                        />
                    </div>

                    {/* Text */}
                    <div className="flex-1 min-w-0">
                        <h4 className="text-[11px] font-semibold text-zinc-200 truncate leading-tight group-hover:text-indigo-200 transition-colors max-w-[130px]">
                            {data.title}
                        </h4>
                        <p className="text-[9px] text-zinc-500 truncate max-w-[130px]">{data.domain}</p>
                    </div>

                    {/* Timestamp badge */}
                    <span className="text-[8px] text-zinc-500 bg-zinc-900/60 px-1.5 py-0.5 rounded font-medium shrink-0">
                        {data.timestamp}
                    </span>
                </div>
            </motion.div>
        </>
    );
};

export default CognitiveMapNode;
