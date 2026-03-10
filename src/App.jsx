import React, { useState, useEffect } from 'react';
import FloatingWidget from './components/FloatingWidget';
import SlidingPanel from './components/SlidingPanel';

function App() {
    const [isOpen, setIsOpen] = useState(false);

    // Listen for the Chrome Extension toolbar button click
    useEffect(() => {
        const handleMessage = (request, sender, sendResponse) => {
            if (request.action === "TOGGLE_COS_PANEL") {
                setIsOpen((prev) => !prev);
            }
        };

        if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
            chrome.runtime.onMessage.addListener(handleMessage);
        }

        return () => {
            if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.onMessage) {
                chrome.runtime.onMessage.removeListener(handleMessage);
            }
        };
    }, []);

    return (
        // Top level container is completely transparent and pointer-events-none
        // so it doesn't block interactions on the underlying webpage.
        // Fixed positioning ensures it covers the viewport.
        <div className="fixed inset-0 z-[9999] pointer-events-none bg-transparent">

            {/*
        The actual interactive elements must re-enable pointer events
        so users can click the widget and the panel.
      */}
            <div className="pointer-events-auto">
                <FloatingWidget
                    isOpen={isOpen}
                    onClick={() => setIsOpen(!isOpen)}
                />

                <SlidingPanel
                    isOpen={isOpen}
                    onClose={() => setIsOpen(false)}
                />
            </div>

        </div>
    );
}

export default App;
