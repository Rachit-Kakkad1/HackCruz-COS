/**
 * COS — Premium Popup Script.
 */

const BACKEND_URL = "http://localhost:8000";

const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const recallBtn = document.getElementById("recall-btn");
const timelineBtn = document.getElementById("timeline-btn");
const graphBtn = document.getElementById("graph-btn");
const resultCard = document.getElementById("result-card");
const resultTitle = document.getElementById("result-title");
const resultUrl = document.getElementById("result-url");
const resultSummary = document.getElementById("result-summary");
const resultTime = document.getElementById("result-time");
const errorMsg = document.getElementById("error-msg");
const pauseBtn = document.getElementById("pause-btn");
const pauseText = document.getElementById("pause-text");

// Identity elements
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const userProfile = document.getElementById("user-profile");
const userName = document.getElementById("user-name");
const userEmail = document.getElementById("user-email");
const userAvatar = document.getElementById("user-avatar");
const resetBtn = document.getElementById("reset-btn");
const privacyBtn = document.getElementById("privacy-btn");

// ─── Health check ────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, { method: "GET" });
    if (res.ok) {
      statusDot.classList.add("connected");
      statusText.textContent = "Engine Online";
      return true;
    }
  } catch (e) {
    // offline
  }
  statusDot.classList.remove("connected");
  statusText.textContent = "Engine Offline";
  return false;
}

// ─── Semantic Recall ─────────────────────────────────────────────────────
async function recallContext() {
  recallBtn.disabled = true;
  recallBtn.style.opacity = "0.7";
  errorMsg.style.display = "none";
  resultCard.classList.remove("visible");

  try {
    const res = await fetch(`${BACKEND_URL}/recall`, { method: "GET" });
    if (!res.ok) throw new Error("Server error");
    const data = await res.json();

    if (data.title) {
      resultTitle.textContent = data.title;
      resultUrl.textContent = data.url ? new URL(data.url).hostname : "local";
      resultUrl.href = data.url || "#";
      resultSummary.textContent = data.summary || "No textual context available.";
      
      const dt = new Date(data.timestamp);
      resultTime.textContent = dt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      
      resultCard.classList.add("visible");
    } else {
      showError("No context captured yet.");
    }
  } catch (err) {
    showError("Could not connect to Core Engine.");
  } finally {
    recallBtn.disabled = false;
    recallBtn.style.opacity = "1";
  }
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = "block";
}

// ─── Navigation ──────────────────────────────────────────────────────────
timelineBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("timeline.html") });
});

graphBtn.addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("graph.html") });
});

recallBtn.addEventListener("click", recallContext);

// Initial call
checkHealth();

// Privacy Toggle
chrome.storage.local.get("monitoringPaused", ({ monitoringPaused }) => {
  if (monitoringPaused) {
    pauseText.textContent = "Resume Monitoring";
    pauseBtn.querySelector('.btn-icon').textContent = "▶️";
  }
});

pauseBtn.addEventListener("click", () => {
  chrome.storage.local.get("monitoringPaused", ({ monitoringPaused }) => {
    const newState = !monitoringPaused;
    chrome.storage.local.set({ monitoringPaused: newState }, () => {
      pauseText.textContent = newState ? "Resume Monitoring" : "Pause Monitoring";
      pauseBtn.querySelector('.btn-icon').textContent = newState ? "▶️" : "⏸️";
    });
  });
});

// ─── Identity layer ──────────────────────────────────────────────────────

function displayUser(user) {
  if (user && user.name) {
    loginBtn.style.display = "none";
    logoutBtn.style.display = "block";
    userProfile.style.display = "flex";
    userName.textContent = user.name;
    userEmail.textContent = user.email;
    userAvatar.src = user.picture || "";
  } else {
    loginBtn.style.display = "block";
    logoutBtn.style.display = "none";
    userProfile.style.display = "none";
  }
}

chrome.storage.local.get("user", ({ user }) => {
  displayUser(user);
});

loginBtn.addEventListener("click", () => {
  // We wrap this in try-catch because without a real Client ID in manifest, it might throw an error.
  try {
    chrome.identity.getAuthToken({ interactive: true }, function(token) {
      if (chrome.runtime.lastError || !token) {
        console.warn("Auth error or cancelled:", chrome.runtime.lastError);
        return;
      }
      
      fetch("https://www.googleapis.com/oauth2/v2/userinfo", {
        headers: { Authorization: "Bearer " + token }
      })
      .then(res => res.json())
      .then(user => {
        chrome.storage.local.set({ user: user, authToken: token });
        displayUser(user);
      })
      .catch(err => console.error("Failed to fetch user info", err));
    });
  } catch (err) {
    console.error("Identity API error:", err);
  }
});

logoutBtn.addEventListener("click", () => {
  chrome.storage.local.get("authToken", ({ authToken }) => {
    if (authToken) {
      chrome.identity.removeCachedAuthToken({ token: authToken }, () => {
        chrome.storage.local.remove(["user", "authToken"], () => {
          displayUser(null);
        });
      });
    } else {
      chrome.storage.local.remove(["user", "authToken"], () => {
        displayUser(null);
      });
    }
  });
});

// ─── Settings ────────────────────────────────────────────────────────

resetBtn.addEventListener("click", () => {
  if (confirm("Are you sure you want to clear all your local memory? This cannot be undone.")) {
    fetch(`${BACKEND_URL}/reset`, { method: "POST" })
      .then(res => res.json())
      .then(data => alert("Memory cleared locally."))
      .catch(err => alert("Failed to reach backend memory store."));
  }
});

privacyBtn.addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("consent.html") });
});
