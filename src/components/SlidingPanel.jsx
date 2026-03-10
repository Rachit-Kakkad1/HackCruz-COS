import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Search, Filter, LayoutDashboard, Clock, BrainCircuit } from 'lucide-react';
import Timeline from './Timeline';
import TimeGraph from './TimeGraph';
import FocusScore from './FocusScore';
import ClusterView from './ClusterView';
import ConsentScreen from './ConsentScreen';
import CognitiveMap from './CognitiveMap';
import { getExtensionUrl } from '../utils';

// ─── TAB DEFINITIONS ─────────────────────────────────────────────────────────
const TABS = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'cognitive-map', label: 'Cognitive Map', icon: BrainCircuit },
];

const SlidingPanel = ({ isOpen, onClose }) => {
    const [isFocusLocked, setIsFocusLocked] = useState(false);
    const [hasConsent, setHasConsent] = useState(null); // null means loading
    const [activeTab, setActiveTab] = useState('dashboard');

    useEffect(() => {
        // Read initial consent state
        if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
            chrome.storage.local.get(['cos_consent'], (result) => {
                setHasConsent(!!result.cos_consent);
            });
        } else {
            // Local dev fallback
            const localConsent = localStorage.getItem('cos_consent');
            setHasConsent(localConsent === 'true');
        }
    }, [isOpen]);

    const handleConsentGranted = () => {
        if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
            chrome.storage.local.set({ cos_consent: true }, () => {
                setHasConsent(true);
            });
        } else {
            // Local dev fallback
            localStorage.setItem('cos_consent', 'true');
            setHasConsent(true);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ x: '100%', opacity: 0, scale: 0.95 }}
                    animate={{ x: 0, opacity: 1, scale: 1 }}
                    exit={{ x: '100%', opacity: 0, scale: 0.95 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                    // "Sider" aesthetic: floating card, right-aligned, with margins so it doesn't touch the very edges
                    className="fixed top-4 right-4 bottom-4 z-[10000] w-[28vw] min-w-[380px] max-w-lg glass-panel rounded-2xl flex flex-col shadow-2xl overflow-hidden border border-white/10 pointer-events-auto"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-4 border-b border-white/5 bg-zinc-900/60 backdrop-blur-md z-20">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 flex-shrink-0 rounded-lg flex items-center justify-center overflow-hidden shadow-[0_0_10px_rgba(99,102,241,0.2)]">
                                <img src={getExtensionUrl("logo.png")} alt="COS Logo" className="w-full h-full object-cover rounded-lg" />
                            </div>
                            <h2 className="text-base font-semibold text-zinc-100 tracking-tight">Context Scope</h2>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <button className="p-1.5 text-zinc-400 hover:text-indigo-300 hover:bg-indigo-500/10 rounded-md transition-colors" title="Search Context">
                                <Search className="w-4 h-4" />
                            </button>
                            <button className="p-1.5 text-zinc-400 hover:text-indigo-300 hover:bg-indigo-500/10 rounded-md transition-colors" title="Filter Timeline">
                                <Filter className="w-4 h-4" />
                            </button>
                            <div className="w-px h-4 bg-zinc-800 mx-1"></div>
                            <button
                                onClick={onClose}
                                className="p-1.5 text-zinc-400 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-colors"
                                title="Close Panel"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Content Area */}
                    {hasConsent === null ? (
                        <div className="flex-1" /> // Loading storage state
                    ) : hasConsent === false ? (
                        <ConsentScreen onConsentGranted={handleConsentGranted} />
                    ) : (
                        <>
                            {/* ── Tab Navigation Bar ── */}
                            <div className="flex items-center border-b border-white/5 bg-zinc-900/40 backdrop-blur-sm px-2 shrink-0">
                                {TABS.map(tab => {
                                    const Icon = tab.icon;
                                    const isActive = activeTab === tab.id;
                                    return (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id)}
                                            className={`relative flex items-center gap-1.5 px-3 py-2.5 text-[11px] font-medium tracking-wide transition-colors ${isActive
                                                ? 'text-indigo-300'
                                                : 'text-zinc-500 hover:text-zinc-300'
                                                }`}
                                        >
                                            <Icon className="w-3.5 h-3.5" />
                                            {tab.label}
                                            {/* Active indicator bar */}
                                            {isActive && (
                                                <motion.div
                                                    layoutId="cos-tab-indicator"
                                                    className="absolute bottom-0 left-2 right-2 h-[2px] bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.6)]"
                                                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                                                />
                                            )}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* ── Tab Content ── */}

                            {/* Dashboard Tab — original content, untouched */}
                            {activeTab === 'dashboard' && (
                                <div className="flex-1 overflow-y-auto overflow-x-hidden relative scroll-smooth flex flex-col pb-8">

                                    {/* INSIGHT CARD */}
                                    <div className="mx-5 mt-5">
                                        <motion.div
                                            initial={{ opacity: 0, y: -10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 0.2 }}
                                            className="glass-card rounded-xl p-3 flex items-center gap-3 border border-indigo-500/20 bg-indigo-500/5 shadow-[0_4px_20px_-4px_rgba(99,102,241,0.1)]"
                                        >
                                            <div className="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                                                <span className="text-[10px] text-indigo-400 font-bold">💡</span>
                                            </div>
                                            <p className="text-xs text-zinc-300">You switched context <span className="text-indigo-400 font-semibold">12 times</span> in the last hour.</p>
                                        </motion.div>
                                    </div>

                                    {/* Focus Lock Mode Toggle */}
                                    <div className="mx-5 mt-4 glass-card rounded-xl p-4 flex items-center justify-between border border-white/5 shadow-sm">
                                        <div>
                                            <h3 className="text-sm font-semibold text-zinc-200">Focus Lock Mode</h3>
                                            <p className="text-[11px] text-zinc-500 mt-0.5 tracking-wide">Blocks distracting websites</p>
                                        </div>

                                        <button
                                            onClick={() => setIsFocusLocked(!isFocusLocked)}
                                            className={isFocusLocked
                                                ? "relative inline-flex h-6 w-11 items-center shrink-0 cursor-pointer rounded-full transition-colors duration-300 ease-in-out focus:outline-none bg-indigo-500 shadow-[0_0_12px_rgba(99,102,241,0.5)] border border-indigo-400/50"
                                                : "relative inline-flex h-6 w-11 items-center shrink-0 cursor-pointer rounded-full transition-colors duration-300 ease-in-out focus:outline-none bg-zinc-700 border border-zinc-600"
                                            }
                                        >
                                            <div
                                                className={isFocusLocked
                                                    ? "inline-block h-4 w-4 transform rounded-full bg-white shadow-[0_0_10px_rgba(255,255,255,0.9)] transition-transform duration-300 ease-in-out"
                                                    : "inline-block h-4 w-4 transform rounded-full bg-zinc-300 border-[1.5px] border-zinc-500 shadow-sm transition-transform duration-300 ease-in-out"
                                                }
                                                style={{ transform: isFocusLocked ? 'translateX(22px)' : 'translateX(4px)' }}
                                            />
                                        </button>
                                    </div>

                                    {/* Top Analytics Section (TimeGraph + FocusScore) */}
                                    <div className="p-5 pb-0 flex gap-4">
                                        <TimeGraph />
                                        <FocusScore />
                                    </div>

                                    {/* Context Cluster */}
                                    <div className="px-5 mt-4">
                                        <ClusterView />
                                    </div>

                                    {/* Advanced Timeline Section */}
                                    <div className="flex-1 mt-6">
                                        <div className="px-5 flex items-center justify-between mb-2">
                                            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Activity History</h3>

                                            {/* LIVE SYSTEM FEEL (Pulsing Dot) */}
                                            <div className="flex items-center gap-1.5 bg-zinc-800/40 border border-zinc-700/50 px-2 py-0.5 rounded-md">
                                                <span className="relative flex h-2 w-2">
                                                    <motion.span
                                                        animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.5, 1] }}
                                                        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                                                        className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"
                                                    />
                                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
                                                </span>
                                                <span className="text-[10px] text-zinc-400 tracking-wide font-medium">Live</span>
                                            </div>
                                        </div>
                                        <Timeline />
                                    </div>
                                </div>
                            )}

                            {/* Timeline Tab — full-height Timeline */}
                            {activeTab === 'timeline' && (
                                <div className="flex-1 overflow-y-auto overflow-x-hidden relative scroll-smooth flex flex-col pb-8">
                                    <div className="flex-1 mt-2">
                                        <div className="px-5 flex items-center justify-between mb-2 mt-3">
                                            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Full Timeline</h3>
                                            <div className="flex items-center gap-1.5 bg-zinc-800/40 border border-zinc-700/50 px-2 py-0.5 rounded-md">
                                                <span className="relative flex h-2 w-2">
                                                    <motion.span
                                                        animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.5, 1] }}
                                                        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                                                        className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"
                                                    />
                                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
                                                </span>
                                                <span className="text-[10px] text-zinc-400 tracking-wide font-medium">Live</span>
                                            </div>
                                        </div>
                                        <Timeline />
                                    </div>
                                </div>
                            )}

                            {/* Cognitive Map Tab */}
                            {activeTab === 'cognitive-map' && (
                                <div className="flex-1 flex flex-col overflow-hidden">
                                    <CognitiveMap />
                                </div>
                            )}
                        </>
                    )}

                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default SlidingPanel;
