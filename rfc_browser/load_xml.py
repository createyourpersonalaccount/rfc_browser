import xml.etree.ElementTree as ET
import networkx as nx

tree = ET.parse("../rfc-index.xml")
root = tree.getroot()
ns = {"": "https://www.rfc-editor.org/rfc-index"}

class RFC:
    def __init__(self, el):
        self.id = el.find('doc-id', ns).text
        self.title = child.find('title', ns).text
        self.date = child.find('date', ns).find('year', ns).text
        self.current_status = child.find('current-status', ns).text
        # Have to filter these to only contain RFCs.
        self.updates = [
            update.text for update in child.find('updates', ns) or [] if update.text.startswith("RFC")
        ]
        self.updated_by = [
            updated.text for updated in child.find('updated-by', ns) or [] if updated.text.startswith("RFC")
        ]
        self.obsoletes = [
            obsolete.text for obsolete in child.find('obsoletes', ns) or [] if obsolete.text.startswith("RFC")
        ]
        self.obsoleted_by = [
            obsoleted.text for obsoleted in child.find('obsoleted-by', ns) or [] if obsoleted.text.startswith("RFC")
        ]
        self.stream = child.find('stream', ns).text
        self.doi = child.find('doi', ns).text

def style_graph(a):
    for node in a.nodes():
        node.attr["URL"] = f"https://www.rfc-editor.org/info/{node.lower()}"
        match rfcs[node].current_status:
            case "INTERNET STANDARD":
                node.attr["shape"] = "box"
                node.attr["label"] = f"{node}\nSTD"
                node.attr["fillcolor"] = "cornflowerblue"
                node.attr["style"] = "filled"
            case "DRAFT STANDARD":
                node.attr["shape"] = "double circle"
                node.attr["label"] = f"{node}\nDRAFT"
            case "PROPOSED STANDARD":
                node.attr["shape"] = "ellipse"
                node.attr["label"] = f"{node}\nPROPOSED"
                node.attr["fillcolor"] = "cornflowerblue"
                node.attr["style"] = "filled"
            case "UNKNOWN":
                node.attr["shape"] = "plaintext"
                node.attr["label"] = f"{node}\nUNKNOWN"
            case "BEST CURRENT PRACTICE":
                node.attr["shape"] = "diamond"
                node.attr["label"] = f"{node}\nBEST PRACTICE"
            case "FOR YOUR INFORMATION":
                node.attr["shape"] = "house"
                node.attr["label"] = f"{node}\nFYI"
            case "EXPERIMENTAL":
                node.attr["shape"] = "invhouse"
                node.attr["label"] = f"{node}\nEXPERIMENTAL"
            case "HISTORIC":
                node.attr["shape"] = "folder"
                node.attr["label"] = f"{node}\nHISTORIC"
            case "INFORMATIONAL":
                node.attr["shape"] = "cds"
                node.attr["label"] = f"{node}\nINFO"
            case _:
                continue
    for edge in a.edges():
        if obg.has_edge(*edge):
            edge.attr["style"] = "dotted"

rfcs = {}

for child in root.findall('rfc-entry', ns):
    rfc = RFC(child)
    rfcs[rfc.id] = rfc

nodes = nx.DiGraph()
ug = nx.DiGraph()
ubg = nx.DiGraph()
og = nx.DiGraph()
obg = nx.DiGraph()

for rfc in rfcs.values():
    nodes.add_node(rfc.id)

ug.add_nodes_from(nodes)
ubg.add_nodes_from(nodes)
og.add_nodes_from(nodes)
obg.add_nodes_from(nodes)

for rfc in rfcs.values():
    for k in rfc.updates:
        ug.add_edge(rfc.id, k)
    for k in rfc.updated_by:
        ubg.add_edge(rfc.id, k)
    for k in rfc.obsoletes:
        og.add_edge(rfc.id, k)
    for k in rfc.obsoleted_by:
        obg.add_edge(rfc.id, k)

# Find the descendants of RFC1034, RFC1035, and RFC1886
c = nx.compose(ubg, obg)
l = []
for r in ["RFC1034", "RFC1035", "RFC1886"]:
    x = nx.descendants(c, r)
    x.add(r)
    l.append(nx.subgraph(c, x))
# Limit the graph to only those RFCs and their descendants
g = nx.compose_all(l)
a = nx.nx_agraph.to_agraph(g)
style_graph(a)
a.write("before_reduction.gv")

t = nx.transitive_reduction(g)
a = nx.nx_agraph.to_agraph(nx.intersection(g, t))
style_graph(a)
a.write("with_obsolete.gv")

g_without = nx.DiGraph()

for u, v in g.edges():
    if obg.has_edge(u, v):
        for x in nx.ancestors(g, u):
            g_without.add_edge(x, v)
    else:
        g_without.add_edge(u, v)

# TODO now we're supposed to transitively reduce but we haven't gotten
# the edge contraction down yet... FIXME.
# t = nx.transitive_reduction(g_without)
# a = nx.nx_agraph.to_agraph(nx.intersection(g_without, t))
a = nx.nx_agraph.to_agraph(g_without)
style_graph(a)
a.write("without_obsolete.gv")
