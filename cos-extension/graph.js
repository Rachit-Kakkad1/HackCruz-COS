const BACKEND_URL = "http://localhost:8000";

let network = null;
const nodesData = new vis.DataSet();
const edgesData = new vis.DataSet();

const detailPanel = document.getElementById("detail-panel");
const closePanelBtn = document.getElementById("close-panel");
const nodeTitleEl = document.getElementById("node-title");
const nodeUrlEl = document.getElementById("node-url");
const nodeSummaryEl = document.getElementById("node-summary");

const rawNodesMap = new Map();

// Helper to determine node color based on keywords
function getNodeColor(title) {
  const t = title.toLowerCase();
  if (t.includes("code") || t.includes("github") || t.includes("api")) {
    return { background: "#1e3a8a", border: "#3b82f6" }; // Blue - Coding
  }
  if (t.includes("research") || t.includes("ai") || t.includes("wiki")) {
    return { background: "#581c87", border: "#a855f7" }; // Purple - Research
  }
  if (t.includes("mail") || t.includes("doc") || t.includes("write")) {
    return { background: "#14532d", border: "#22c55e" }; // Green - Productivity
  }
  return { background: "#1a1a2e", border: "#6b7280" }; // Default - Gray/Glass
}

async function loadGraph() {
  try {
    const res = await fetch(`${BACKEND_URL}/graph`);
    if (!res.ok) throw new Error("Server error");
    const data = await res.json();
    
    document.getElementById("loading").style.display = "none";

    data.nodes.forEach(n => {
      rawNodesMap.set(n.id, n);
      const colors = getNodeColor(n.title);
      nodesData.add({
        id: n.id,
        label: n.title.length > 20 ? n.title.substring(0, 20) + "..." : n.title,
        title: n.title, // hover tooltip
        color: {
          background: colors.background,
          border: colors.border,
          highlight: { background: colors.border, border: "#fff" }
        },
        font: { color: "#eeeeee", face: "Inter" }
      });
    });

    data.edges.forEach(e => {
      edgesData.add({
        from: e.source,
        to: e.target,
        value: e.weight, // thicker line for higher similarity
        title: `Similarity: ${(e.weight * 100).toFixed(1)}%`,
        color: { color: "rgba(110, 124, 255, 0.4)", highlight: "#9A7BFF" },
        smooth: { type: "continuous" }
      });
    });

    initNetwork();

  } catch (err) {
    document.getElementById("loading").textContent = "Failed to load graph data.";
    document.getElementById("loading").style.color = "#FF6B6B";
  }
}

function initNetwork() {
  const container = document.getElementById("mynetwork");
  const data = { nodes: nodesData, edges: edgesData };
  const options = {
    nodes: {
      shape: "dot",
      size: 20,
      borderWidth: 2,
      shadow: { enabled: true, color: "rgba(0,0,0,0.5)", size: 10 }
    },
    edges: {
      width: 2,
      selectionWidth: 3
    },
    physics: {
      forceAtlas2Based: {
        gravitationalConstant: -50,
        centralGravity: 0.01,
        springLength: 100,
        springConstant: 0.08
      },
      maxVelocity: 50,
      solver: "forceAtlas2Based",
      timestep: 0.35,
      stabilization: { iterations: 150 }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200
    }
  };

  network = new vis.Network(container, data, options);

  // Handle click to open detail panel
  network.on("click", function (params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const nodeData = rawNodesMap.get(nodeId);
      
      nodeTitleEl.textContent = nodeData.title;
      nodeUrlEl.textContent = nodeData.url;
      nodeSummaryEl.textContent = nodeData.summary || "No summary available.";
      
      detailPanel.classList.add("open");
      
      // Focus animation
      network.focus(nodeId, {
        scale: 1.2,
        animation: { duration: 400, easingFunction: "easeInOutQuad" }
      });
    } else {
      detailPanel.classList.remove("open");
    }
  });
}

closePanelBtn.addEventListener("click", () => {
  detailPanel.classList.remove("open");
});

document.addEventListener("DOMContentLoaded", loadGraph);
