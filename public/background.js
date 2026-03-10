// ─── COS Backend Configuration ────────────────────────────────────────────
const API_URL = "http://localhost:8000/api/v1/events/track";
const USER_ID = "550e8400-e29b-41d4-a716-446655440000"; // Demo user UUID
const DEDUPE_INTERVAL_MS = 3000; // Ignore duplicate URLs within 3 seconds

let lastSentUrl = "";
let lastSentTime = 0;

// ─── Existing: Toggle COS Panel ───────────────────────────────────────────
chrome.action.onClicked.addListener((tab) => {
    if (tab.id) {
        chrome.tabs.sendMessage(tab.id, { action: "TOGGLE_COS_PANEL" }).catch((error) => {
            console.log("Could not send message to content script:", error);
        });
    }
});

// ─── Event Tracker: Send browsing context to COS backend ──────────────────

/**
 * Extract visible text from the active tab via the scripting API.
 * Returns the first 1000 characters of body text for embedding quality.
 */
async function extractPageText(tabId) {
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId },
            func: () => document.body?.innerText?.slice(0, 1000) || "",
        });
        return results?.[0]?.result || "";
    } catch {
        return ""; // Fails silently for restricted pages (chrome://, etc.)
    }
}

/**
 * Send a browsing event to the COS backend.
 * Includes deduplication to avoid flooding the API with rapid tab switches.
 */
async function sendEvent(tab) {
    if (!tab?.url || !tab.url.startsWith("http")) return;

    // Deduplicate: skip if same URL was sent within DEDUPE_INTERVAL_MS
    const now = Date.now();
    if (tab.url === lastSentUrl && now - lastSentTime < DEDUPE_INTERVAL_MS) return;
    lastSentUrl = tab.url;
    lastSentTime = now;

    // Extract page text for richer embeddings
    let textSnippet = "";
    if (tab.id) {
        textSnippet = await extractPageText(tab.id);
    }

    const payload = {
        userId: USER_ID,
        url: tab.url,
        title: tab.title || "",
        textSnippet,
        timestamp: new Date().toISOString(),
    };

    try {
        await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
    } catch (err) {
        // Backend may be offline — fail silently, don't break browsing
        console.debug("COS tracker: backend unreachable", err.message);
    }
}

// ── Trigger 1: User switches to a different tab ───────────────────────────
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    try {
        const tab = await chrome.tabs.get(activeInfo.tabId);
        sendEvent(tab);
    } catch { }
});

// ── Trigger 2: Page finishes loading ──────────────────────────────────────
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete") {
        sendEvent(tab);
    }
});

// ── Trigger 3: User switches browser windows ─────────────────────────────
chrome.windows.onFocusChanged.addListener(async (windowId) => {
    if (windowId === chrome.windows.WINDOW_ID_NONE) return;
    try {
        const tabs = await chrome.tabs.query({ active: true, windowId });
        if (tabs.length > 0) sendEvent(tabs[0]);
    } catch { }
});
