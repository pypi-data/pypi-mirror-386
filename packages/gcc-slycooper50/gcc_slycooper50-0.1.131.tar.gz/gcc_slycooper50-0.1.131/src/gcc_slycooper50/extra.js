window.addEventListener('load', () => {
  const network = window.network;
  const nodes = window.nodes;
  const edges = window.edges;

  const nodeList = document.getElementById("nodeList");
  const nodeTitle = document.getElementById("nodeTitle");
  const info = document.getElementById("info");
  const save = document.getElementById("save_btt");

  // Build adjacency map
  const adjacency = {};
  edges.get().forEach(e => {
    if (!adjacency[e.from]) adjacency[e.from] = [];
    adjacency[e.from].push(e.to);
  });

  // Update sidebar list with children of a node
  function showChildren(nodeId) {
    nodeList.innerHTML = "";
    nodeTitle.textContent = "Children of " + nodeId;

    const children = adjacency[nodeId] || [];
    if (children.length === 0) {
      const li = document.createElement("li");
      li.textContent = "(no children)";
      li.style.color = "#888";
      nodeList.appendChild(li);
      return;
    }

    children.forEach(childId => {
      const li = document.createElement("li");
      li.textContent = childId;
      li.style.cursor = "pointer";
      li.style.padding = "4px 0";
      li.onmouseenter = () => li.style.color = "#ffcc00";
      li.onmouseleave = () => li.style.color = "";
      li.onclick = () => {
        // Focus and highlight the clicked child
        network.focus(childId, { scale: 1.5, animation: true });
        nodes.update({ id: childId, color: "#ff4444" });
        setTimeout(() => nodes.update({ id: childId, color: "#00ccff" }), 1500);
      };
      nodeList.appendChild(li);
    });
  }

  // --- Event handlers ---
  network.on("click", params => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      showChildren(nodeId);
    }
  });

  network.on("hoverNode", params => {
    info.textContent = "Hovering: " + params.node;
  });

  network.on("blurNode", () => {
    info.textContent = "Click a node to see its children.";
  });
   
  save.addEventListener("click", () => {
	  console.log("SLYCOOPER");
  });

});
