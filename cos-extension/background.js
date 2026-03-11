/**
 * COS — Background Service Worker (Manifest V3).
 *
 * Listens for tab switches, injects the content script to extract
 * visible page text, and POSTs a context snapshot to the local backend.
 */

const BACKEND_URL = "http://localhost:8000";

// --- ON INSTALL: TRIGGER CONSENT ---
chrome.runtime.onInstalled.addListener(() => {
  chrome.tabs.create({
    url: chrome.runtime.getURL("consent.html")
  });
});

/**
 * Clean URL to just domain if it's http/httpse backend.
 */
async function sendSnapshot(payload) {
  try {
    const response = await fetch(`${BACKEND_URL}/context`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    console.log("[COS] Snapshot stored:", data);
  } catch (err) {
    console.warn("[COS] Backend unreachable:", err.message);
  }
}

/**
 * Extract visible text from the active tab by injecting a function.
 * Returns the first 2000 characters of document.body.innerText.
 */
async function extractPageText(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        return document.body ? document.body.innerText.slice(0, 2000) : "";
      },
    });
    if (results && results[0] && results[0].result) {
      return results[0].result;
    }
  } catch (err) {
    console.warn("[COS] Cannot inject script into tab:", err.message);
  }
  return "";
}

/**
 * Handle tab activation: gather context and send to backend.
 */
async function handleTabActivated(activeInfo) {
  const { monitoringPaused, consent } = await chrome.storage.local.get(["monitoringPaused", "consent"]);
  
  if (!consent) {
    console.log("[COS] Monitoring blocked — consent not granted.");
    return;
  }
  
  if (monitoringPaused) {
    console.log("[COS] Monitoring is manually paused. Skipping context capture.");
    return;
  }

  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);

    // Skip chrome:// internal pages and empty tabs
    if (!tab.url || tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) {
      return;
    }

    const text = await extractPageText(tab.id);

    const snapshot = {
      title: tab.title || "Untitled",
      url: tab.url,
      text: text,
      timestamp: new Date().toISOString(),
      app: "chrome",
    };

    console.log("[COS] Tab switch detected:", snapshot.title);
    await sendSnapshot(snapshot);
  } catch (err) {
    console.error("[COS] Error handling tab activation:", err);
  }
}

// ─── Event Listeners ─────────────────────────────────────────────────────

chrome.tabs.onActivated.addListener(handleTabActivated);

// Also capture page loads (when a tab finishes loading new content)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.active) {
    handleTabActivated({ tabId });
  }
});

// Listen for keyboard short (Ctrl+Shift+Space) to trigger floating overlay
chrome.commands.onCommand.addListener(async (command) => {
  if (command === "toggle_overlay") {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    // Inject a script that creates an iframe pointing to our overlay.html
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const existing = document.getElementById("cos-overlay-frame");
        if (existing) {
          existing.remove(); // Toggle off if already exists
          return;
        }

        const iframe = document.createElement("iframe");
        iframe.id = "cos-overlay-frame";
        iframe.src = chrome.runtime.getURL("overlay.html");
        
        // Premium glassmorphism overlay styles
        Object.assign(iframe.style, {
          position: "fixed",
          top: "0",
          left: "0",
          width: "100vw",
          height: "100vh",
          border: "none",
          zIndex: "2147483647", // max z-index
          backgroundColor: "transparent",
          pointerEvents: "auto"
        });

        document.body.appendChild(iframe);

        // Listen for messages from the iframe to close it
        window.addEventListener("message", function listener(event) {
          if (event.data === "CLOSE_COS_OVERLAY") {
            const frame = document.getElementById("cos-overlay-frame");
            if (frame) frame.remove();
            window.removeEventListener("message", listener);
          }
        });
      }
    });
  }
});

console.log("[COS] Background service worker started.");
