const BACKEND_URL = "http://localhost:8000";
const container = document.getElementById("timeline-container");

async function loadTimeline() {
  try {
    const res = await fetch(`${BACKEND_URL}/timeline`);
    if (!res.ok) throw new Error("Server error");
    const data = await res.json();
    
    container.innerHTML = "";
    
    if (!data.timeline || data.timeline.length === 0) {
      container.innerHTML = "<div class='loading'>No cognitive memory captured yet.</div>";
      return;
    }

    data.timeline.forEach((ctx, index) => {
      // Stagger animation delay
      const delay = index * 0.05;
      
      const timeStr = new Date(ctx.timestamp).toLocaleTimeString([], { hour: '2-digit', minute:'2-digit' });
      const domain = ctx.url ? new URL(ctx.url).hostname : "local";
      
      const el = document.createElement("div");
      el.className = "timeline-item";
      el.style.animationDelay = `${delay}s`;
      
      el.innerHTML = `
        <div class="card">
          <div class="card-header">
            <div class="time-badge">${timeStr}</div>
            <div class="domain-badge">
              <img src="https://www.google.com/s2/favicons?domain=${domain}&sz=32" alt="" onerror="this.style.display='none'">
              ${domain}
            </div>
          </div>
          <a href="${ctx.url}" target="_blank">
            <h3>${ctx.title}</h3>
          </a>
          <p>${ctx.summary || 'No text extracted.'}</p>
        </div>
      `;
      
      container.appendChild(el);
    });

  } catch (err) {
    container.innerHTML = "<div class='loading' style='color:#FF6B6B'>Failed to load timeline. Is the backend running?</div>";
  }
}

document.addEventListener("DOMContentLoaded", loadTimeline);
