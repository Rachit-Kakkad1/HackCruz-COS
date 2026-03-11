/**
 * COS — Floating Recall Overlay Script.
 * Displayed in an iframe injected into the active tab via Ctrl+Shift+Space.
 */

const BACKEND_URL = "http://localhost:8000";

const backdrop = document.getElementById("backdrop");
const modal = document.getElementById("modal");
const closeBtn = document.getElementById("close-btn");
const dismissBtn = document.getElementById("dismiss-btn");
const resumeBtn = document.getElementById("resume-btn");

const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");
const contextCard = document.getElementById("context-card");

const ctxTitle = document.getElementById("ctx-title");
const ctxUrl = document.getElementById("ctx-url");
const ctxSummary = document.getElementById("ctx-summary");
const ctxTime = document.getElementById("ctx-time");

let targetUrl = "";

// Trigger initial fade-in via CSS class on load
requestAnimationFrame(() => {
  backdrop.classList.add("visible");
  modal.classList.add("visible");
});

// Instruct parent window to remove the iframe
function closeOverlay() {
  backdrop.classList.remove("visible");
  modal.classList.remove("visible");
  
  // Wait for fade out animation before destroying iframe
  setTimeout(() => {
    window.parent.postMessage("CLOSE_COS_OVERLAY", "*");
  }, 300);
}

// Open context in a new tab
function resumeContext() {
  if (targetUrl) {
    window.open(targetUrl, "_blank");
    closeOverlay();
  }
}

// Fetch semantic recall
async function loadRecall() {
  try {
    const res = await fetch(`${BACKEND_URL}/recall`);
    if (!res.ok) throw new Error("Backend error");
    const data = await res.json();
    
    loadingEl.style.display = "none";
    
    if (data.title && data.title !== "No context yet") {
      ctxTitle.textContent = data.title;
      ctxUrl.textContent = data.url ? new URL(data.url).hostname : "local";
      ctxSummary.textContent = data.summary || "No summary available.";
      
      const dt = new Date(data.timestamp);
      ctxTime.textContent = dt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      
      targetUrl = data.url;
      resumeBtn.disabled = false;
      contextCard.style.display = "block";
    } else {
      errorEl.textContent = "No browsing memory captured yet.";
      errorEl.style.display = "block";
    }

  } catch (err) {
    loadingEl.style.display = "none";
    errorEl.textContent = "Could not connect to Core Engine (Backend Offline).";
    errorEl.style.display = "block";
  }
}

// Event Listeners
closeBtn.addEventListener("click", closeOverlay);
dismissBtn.addEventListener("click", closeOverlay);
resumeBtn.addEventListener("click", resumeContext);
backdrop.addEventListener("click", closeOverlay); // Click outside to close

// Escape key to close
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeOverlay();
});

// Start data fetch
loadRecall();
