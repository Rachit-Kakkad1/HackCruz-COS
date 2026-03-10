import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import TimelineCard from './TimelineCard';
import RecallPopup from './RecallPopup';

// Mock Data
const MOCK_DATA = [
    {
        id: 1,
        timeGroup: 'Just Now',
        favicon: 'https://www.google.com/s2/favicons?domain=mail.google.com&sz=64',
        title: 'Gmail - Hackathon budget draft',
        summary: 'Discussing the final budget allocation for the weekend hackathon event including prizes and food.',
        timestamp: '10:42 AM',
        type: 'mail'
    },
    {
        id: 2,
        timeGroup: 'Just Now',
        favicon: 'https://www.google.com/s2/favicons?domain=youtube.com&sz=64',
        title: 'YouTube - AI research video',
        summary: 'Watched a 20-minute video explaining advanced RAG architectures and vector embeddings.',
        timestamp: '10:15 AM',
        type: 'video'
    },
    {
        id: 3,
        timeGroup: 'Earlier Today',
        favicon: 'https://www.google.com/s2/favicons?domain=docs.google.com&sz=64',
        title: 'Docs - COS planning notes',
        summary: 'Collaborative document outlining the user flow and feature requirements for the Context Operating System.',
        timestamp: '09:30 AM',
        type: 'doc'
    },
    {
        id: 4,
        timeGroup: 'Earlier Today',
        favicon: 'https://www.google.com/s2/favicons?domain=github.com&sz=64',
        title: 'GitHub - cos-extension repo',
        summary: 'Reviewed pull request #42 regarding the sliding panel animation performance fixes.',
        timestamp: '08:45 AM',
        type: 'code'
    }
];

const TimelineLine = () => (
    // The continuous vertical line that runs down the left side
    <div className="absolute left-[27px] top-0 bottom-0 w-px bg-gradient-to-b from-indigo-500/50 via-zinc-700 to-transparent pointer-events-none z-0" />
);

const Timeline = () => {
    const [selectedCard, setSelectedCard] = useState(null);

    // Group data by timeGroup
    const groupedData = MOCK_DATA.reduce((acc, curr) => {
        if (!acc[curr.timeGroup]) acc[curr.timeGroup] = [];
        acc[curr.timeGroup].push(curr);
        return acc;
    }, {});

    return (
        <div className="relative">
            <TimelineLine />

            <div className="px-5 pb-6 space-y-6">
                {Object.entries(groupedData).map(([groupName, items], groupIndex) => (
                    <motion.div
                        key={groupName}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: groupIndex * 0.1, duration: 0.4 }}
                        className="relative z-10"
                    >
                        <div className="flex items-center gap-3 mb-4 sticky top-0 bg-zinc-950/80 backdrop-blur-md py-1 -mx-2 px-2 rounded z-20">
                            {/* Timeline dot for section header */}
                            <div className="w-[7px] h-[7px] rounded-full bg-zinc-600 border-2 border-zinc-950 shrink-0 shadow-[0_0_0_4px_rgba(9,9,11,1)]" />
                            <span className="text-[10px] font-bold text-zinc-400/80 uppercase tracking-widest">{groupName}</span>
                        </div>

                        {/* 4. STAGGER ENTRY ANIMATION (Container) */}
                        <motion.div
                            className="space-y-3"
                            initial="hidden"
                            animate="visible"
                            variants={{
                                hidden: {},
                                visible: {
                                    transition: { staggerChildren: 0.1 }
                                }
                            }}
                        >
                            {items.map((item, idx) => (
                                <TimelineCard
                                    key={item.id}
                                    data={item}
                                    onClick={() => setSelectedCard(item)}
                                // Remove manual transition index, handled by staggerChildren in TimelineCard variants
                                />
                            ))}
                        </motion.div>
                    </motion.div>
                ))}
            </div>

            <RecallPopup
                isOpen={!!selectedCard}
                data={selectedCard}
                onClose={() => setSelectedCard(null)}
            />
        </div>
    );
};

export default Timeline;
