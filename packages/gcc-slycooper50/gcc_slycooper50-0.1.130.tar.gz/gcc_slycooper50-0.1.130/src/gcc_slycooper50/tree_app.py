from pyvis.network import Network
import json

# ---------------------------
# Tree data
# ---------------------------
tree_data = {
    "Root": {"type": "root", "value": 10, "children": ["Child 1", "Child 2", "Child 3"]},

    "Child 1": {"type": "branch", "value": 5, "children": ["Grandchild 1.1", "Grandchild 1.2"]},
    "Child 2": {"type": "branch", "value": 7, "children": ["Grandchild 2.1", "Grandchild 2.2"]},
    "Child 3": {"type": "branch", "value": 6, "children": ["Grandchild 3.1"]},

    "Grandchild 1.1": {"type": "leaf", "value": 3, "children": []},
    "Grandchild 1.2": {"type": "leaf", "value": 4, "children": [], "highlight": True},

    "Grandchild 2.1": {"type": "branch", "value": 2, "children": ["GreatGrandchild 2.1.1"]},
    "Grandchild 2.2": {"type": "leaf", "value": 4, "children": []},

    "Grandchild 3.1": {"type": "branch", "value": 5, "children": ["GreatGrandchild 3.1.1", "GreatGrandchild 3.1.2"]},

    "GreatGrandchild 2.1.1": {"type": "leaf", "value": 1, "children": [], "highlight": True},
    "GreatGrandchild 3.1.1": {"type": "leaf", "value": 2, "children": []},
    "GreatGrandchild 3.1.2": {"type": "leaf", "value": 3, "children": [], "highlight": True},
}

# ---------------------------
# Positions for layout (x,y)
# ---------------------------
positions = {
    "Root": (0, 0),
    "Child 1": (-300, 150),
    "Child 2": (0, 150),
    "Child 3": (300, 150),

    "Grandchild 1.1": (-400, 300),
    "Grandchild 1.2": (-200, 300),

    "Grandchild 2.1": (-50, 300),
    "Grandchild 2.2": (50, 300),

    "Grandchild 3.1": (300, 300),

    "GreatGrandchild 2.1.1": (-50, 450),
    "GreatGrandchild 3.1.1": (250, 450),
    "GreatGrandchild 3.1.2": (350, 450),
}

colors = {"root": "#ffcc00", "branch": "#66ccff", "leaf": "#99ff99"}

# ---------------------------
# Build Pyvis Network
# ---------------------------
#net = Network(height="600px", width="100%", directed=True, notebook=False)

net = Network(
    height="600px",
    width="100%",
    directed=True,
    notebook=False,
    cdn_resources='remote'  # <-- load JS via CDN, avoids utils.js errors
)
net.toggle_physics(False)

for name, props in tree_data.items():
    x, y = positions[name]
    node_color = "red" if props.get("highlight") else colors[props["type"]]
    net.add_node(name, label=name, x=x, y=y, fixed=False, color=node_color, size=25)

for parent, props in tree_data.items():
    for child in props["children"]:
        net.add_edge(parent, child, arrows='to', smooth={'type': 'cubicBezier', 'roundness': 0.4})

# Generate HTML
html = net.generate_html()

# ---------------------------
# Extra sidebar JS/CSS
# ---------------------------
extra_js = f"""
<style>
#sidebar {{
    position: absolute;
    left: 10px;
    top: 10px;
    width: 250px;
    background: #f8f8f8;
    padding: 10px;
    border-radius: 10px;
    box-shadow: 0 0 8px rgba(0,0,0,0.2);
    font-family: Arial;
}}
#menuBar button {{
    margin: 3px;
    padding: 5px 8px;
    border: none;
    background: #ddd;
    border-radius: 4px;
    cursor: pointer;
}}
#menuBar button:hover {{
    background: #ccc;
}}
#expandMenu {{
    display: none;
    position: absolute;
    background: white;
    border: 1px solid #aaa;
    box-shadow: 0 0 5px rgba(0,0,0,0.2);
    border-radius: 5px;
    padding: 5px;
    margin-top: 5px;
    z-index: 1000;
}}
#expandMenu div {{
    padding: 5px;
    cursor: pointer;
}}
#expandMenu div:hover {{
    background: #eee;
}}
#saveButton {{
    width: 100%;
    margin-top: 10px;
    padding: 8px;
    border: none;
    background: #4CAF50;
    color: white;
    font-weight: bold;
    border-radius: 6px;
    cursor: pointer;
}}
#saveButton:hover {{
    background: #45a049;
}}
</style>

<div id="sidebar">
  <h3 style="text-align:center;">Node Details</h3>
  <div id="nodeInfo">
    <p><b>Click a node</b> to view details.</p>
  </div>
  <hr>
  <div id="menuBar" style="display:none; text-align:center;">
      <button onclick="menuAction('edit')">✏️ Edit</button>
      <button onclick="menuAction('delete')">🗑️ Delete</button>
      <button id="expandBtn" onclick="menuAction('expand')">🔽 Expand</button>
  </div>
  <div id="expandMenu"></div>
  <button id="saveButton" onclick="saveTree()">💾 Save Tree</button>
</div>

<script>
var treeData = {json.dumps(tree_data)};

// Recursive red propagation
function updateRedness() {{
    const redNodes = new Set();
    function isRed(nodeId) {{
        const node = treeData[nodeId];
        if(node.children.length === 0) return !!node.highlight;
        for(let c of node.children) {{
            if(isRed(c)) return true;
        }}
        return false;
    }}
    for(let nodeId in treeData) {{
        if(isRed(nodeId)) redNodes.add(nodeId);
    }}
    network.body.data.nodes.forEach(n => {{
        let baseColor = (treeData[n.id].type === 'root') ? "#ffcc00" :
                        (treeData[n.id].type === 'branch') ? "#66ccff" : "#99ff99";
        n.color = redNodes.has(n.id) ? "red" : baseColor;
    }});
    network.redraw();
}}

// Node click → sidebar
network.on("click", function(params){{
    hideExpandMenu();
    if(params.nodes.length > 0){{
        var nodeId = params.nodes[0];
        var node = treeData[nodeId];
        document.getElementById("nodeInfo").innerHTML =
            "<p><b>Name:</b> " + nodeId + "</p>" +
            "<p><b>Type:</b> " + node.type + "</p>" +
            "<p><b>Value:</b> " + node.value + "</p>" +
            "<p><b>Children:</b> " + (node.children.join(", ") || "None") + "</p>";
        document.getElementById("menuBar").style.display = "block";
        document.getElementById("menuBar").setAttribute("data-node", nodeId);
    }}
}});

// Menu actions
function menuAction(action){{
    var nodeId = document.getElementById("menuBar").getAttribute("data-node");
    if(action === 'expand') showExpandMenu(treeData[nodeId]);
    else if(action === 'delete') deleteNode(nodeId);
    else alert(action + " action on node: " + nodeId);
}}

// Expand menu
function showExpandMenu(node){{
    var menu = document.getElementById("expandMenu");
    menu.innerHTML = "";
    if(node.children.length === 0){{
        menu.innerHTML = "<div><i>No children</i></div>";
    }} else {{
        node.children.forEach(c => {{
            var item = document.createElement("div");
            item.textContent = c;
            if(treeData[c] && treeData[c].highlight){{
                item.style.color = "red";
                item.style.fontWeight = "bold";
            }}
            item.onclick = function(){{ alert("Selected child: " + c); hideExpandMenu(); }};
            menu.appendChild(item);
        }});
    }}
    var expandBtn = document.getElementById("expandBtn");
    var rect = expandBtn.getBoundingClientRect();
    menu.style.left = rect.left + "px";
    menu.style.top = (rect.bottom + window.scrollY) + "px";
    menu.style.display = "block";
}}

function hideExpandMenu(){{ document.getElementById("expandMenu").style.display = "none"; }}
window.addEventListener('click', function(e){{
    var menu = document.getElementById("expandMenu");
    if(!menu.contains(e.target) && e.target.id !== 'expandBtn') hideExpandMenu();
}});

// Delete node
function deleteNode(nodeId){{
    if(confirm("Delete node '" + nodeId + "'?")){{
        for(let key in treeData){{
            let idx = treeData[key].children.indexOf(nodeId);
            if(idx !== -1) treeData[key].children.splice(idx, 1);
        }}
        delete treeData[nodeId];
        network.body.data.nodes.remove({{id: nodeId}});
        document.getElementById("nodeInfo").innerHTML = "<p><b>Click a node</b> to view details.</p>";
        document.getElementById("menuBar").style.display = "none";
        hideExpandMenu();
        updateRedness();
    }}
}}

// Save tree
function saveTree(){{
    const jsonData = JSON.stringify(treeData, null, 2);
    const blob = new Blob([jsonData], {{ type: "application/json" }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "tree_data.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}}

// Initial red calculation
updateRedness();
</script>
"""

with open("tree.html", "w") as f:
    f.write(html.replace("</body>", extra_js + "</body>"))

print("✅ Open tree.html in your browser")

