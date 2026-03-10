import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

const rootId = 'cos-extension-root';
let isMounted = false;
let currentUrl = location.href;

function initCosMount() {
    let rootContainer = document.getElementById(rootId);

    // 1. Create and firmly anchor the outer container
    if (!rootContainer) {
        rootContainer = document.createElement('div');
        rootContainer.id = rootId;

        // Position the outer root out of the document flow defensively so SPAs can't break its layout
        rootContainer.style.setProperty('position', 'fixed', 'important');
        rootContainer.style.setProperty('top', '0', 'important');
        rootContainer.style.setProperty('right', '0', 'important');
        rootContainer.style.setProperty('height', '100vh', 'important');
        rootContainer.style.setProperty('z-index', '999999', 'important');
        rootContainer.style.setProperty('transform', 'none', 'important');
        rootContainer.style.setProperty('pointer-events', 'none', 'important');

        document.body.appendChild(rootContainer);
    }

    // 2. Attach Shadow DOM (Idempotent)
    let shadowRoot = rootContainer.shadowRoot;
    if (!shadowRoot) {
        shadowRoot = rootContainer.attachShadow({ mode: 'open' });

        // Inject base reset styles to protect from global leaking
        const resetStyle = document.createElement('style');
        resetStyle.textContent = `
            :host {
                all: initial;
                font-family: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
                font-size: 16px;
                color: #d4d4d8;
                box-sizing: border-box;
            }
            *, *::before, *::after {
                box-sizing: border-box;
            }
        `;
        shadowRoot.appendChild(resetStyle);
    }

    // 3. Load Tailwind CSS into Shadow DOM
    const loadStylesIntoShadow = () => {
        try {
            if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.getURL) {
                // Production Chrome Extension
                if (!shadowRoot.querySelector('link[href*="content.css"]')) {
                    const link = document.createElement('link');
                    link.rel = 'stylesheet';
                    link.href = chrome.runtime.getURL('content.css');
                    shadowRoot.appendChild(link);
                }
                return;
            }
        } catch (e) {
            console.warn("COS: Extension context invalidated. Please reload the page.", e);
        }

        // Local Vite Dev Server styles mirror
        const mirrorStyles = () => {
            document.querySelectorAll('style').forEach(style => {
                if (!Array.from(shadowRoot.querySelectorAll('style')).some(s => s.innerHTML === style.innerHTML)) {
                    shadowRoot.appendChild(style.cloneNode(true));
                }
            });
        };
        const observer = new MutationObserver(mirrorStyles);
        observer.observe(document.head, { childList: true });
        mirrorStyles();
    };
    loadStylesIntoShadow();

    // 4. Create application mount point inside the Shadow
    let appRoot = shadowRoot.getElementById('app-root');
    if (!appRoot) {
        appRoot = document.createElement('div');
        appRoot.id = 'app-root';
        // Style appRoot to cover screen but allow pointer events to pass through background
        appRoot.style.setProperty('position', 'fixed', 'important');
        appRoot.style.setProperty('inset', '0', 'important');
        appRoot.style.setProperty('width', '100vw', 'important');
        appRoot.style.setProperty('height', '100vh', 'important');
        appRoot.style.setProperty('pointer-events', 'none', 'important');
        shadowRoot.appendChild(appRoot);
    }

    // Only render React if it hasn't been mounted to this specific exact appRoot reference yet
    if (!appRoot.hasAttribute('data-cos-mounted')) {
        ReactDOM.createRoot(appRoot).render(
            <React.StrictMode>
                <App />
            </React.StrictMode>,
        );
        appRoot.setAttribute('data-cos-mounted', 'true');
    }
}

// Initial Mount Trigger
initCosMount();

// 5. Watch for SPA URL changes and aggressive DOM wipes (e.g. YouTube Navigation)
const observer = new MutationObserver((mutations) => {
    // Re-mount if we detect the URL changed (SPA Soft Navigation)
    if (location.href !== currentUrl) {
        currentUrl = location.href;
        initCosMount();
        return;
    }

    // Defensive check: Re-mount if the host website deleted our container completely from the DOM
    if (!document.getElementById(rootId)) {
        initCosMount();
    }
});

// Start watching the body for destructive layout mutations
if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
} else {
    // If the extension script injected before the body exists, wait for it
    document.addEventListener('DOMContentLoaded', () => {
        initCosMount();
        observer.observe(document.body, { childList: true, subtree: true });
    });
}
