from pyvis.network import Network
from pathlib import Path

# --- Create network ---
net = Network(height="100vh", width="100%", directed=True, bgcolor="#222222", font_color="white")

edges = [
    ("Root", "Child1"),
    ("Root", "Child2"),
    ("Root", "Child3"),
    ("Child1", "Sub1"),
    ("Child1", "Sub2"),
    ("Child2", "Sub3"),
    ("Child3", "Sub4"),
    ("Child3", "Sub5"),
]

# Collect unique nodes
all_nodes = set([n for e in edges for n in e])
for n in all_nodes:
    net.add_node(n, color="#00ccff" if n != "Root" else "#ffcc00")

for src, dst in edges:
    net.add_edge(src, dst)

# Curvy edges + physics
net.set_options("""
{
  "edges": {
    "smooth": {
      "type": "curvedCW",
      "roundness": 0.3
    }
  },
  "physics": {
    "stabilization": false
  }
}
""")

# Save base template
net.save_graph("template.html")

# --- Inject sidebar and JS ---
with open("template.html", "r") as f:
    html = f.read()

sidebar_html = """
<div id="sidebar" style="
  position: fixed;
  left: 10px;
  top: 10px;
  width: 240px;
  height: 95vh;
  background: #2c2c2c;
  color: white;
  padding: 12px;
  border-radius: 8px;
  font-family: sans-serif;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 10px rgba(0,0,0,0.4);
">
  <h3 style="margin-top: 0;">Graph Controls</h3>

  <hr style="border: 0; border-top: 1px solid #555; margin: 8px 0;">
  <h4 id="nodeTitle" style="margin: 4px 0;">Children</h4>
  <div id="nodeContainer" style="
      flex: 1;
      overflow-y: auto;
      border: 1px solid #555;
      border-radius: 6px;
      background: #1e1e1e;
      padding: 6px;
      scrollbar-width: thin;
      scrollbar-color: #666 #2c2c2c;
  ">
      <ul id="nodeList" style="
          list-style: none;
          padding-left: 0;
          margin: 0;
      "></ul>
  </div>

  <hr style="border: 0; border-top: 1px solid #555; margin: 8px 0;">
  <p id="info" style="font-size: 14px; color: #ccc;">Click a node to see its children.</p>

  <div style="display: flex; gap: 10px; margin-bottom: 12px;">
  <button id="del_node">Delete Node</button>
  </div>

  <button id="save_btt">Save New Connections</button>
</div>
"""

html = html.replace("</body>", f"{sidebar_html}\n<script src={str(Path(__file__).resolve().parent)+"/"+"extra.js"}></script>\n</body>")

with open("index.html", "w") as f:
    f.write(html)

print("✅ Created index.html with child-list sidebar.")
