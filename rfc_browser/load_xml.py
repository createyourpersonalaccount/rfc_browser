from importlib.resources import files
import xml.etree.ElementTree as ET
import networkx as nx
import networkx.readwrite.json_graph as json_graph
import json
import sys

ns = {"": "https://www.rfc-editor.org/rfc-index"}
rfcs = {}
nodes = nx.DiGraph()
ug = nx.DiGraph()
ubg = nx.DiGraph()
og = nx.DiGraph()
obg = nx.DiGraph()


class RFC:
    def __init__(self, child):
        self.id = child.find("doc-id", ns).text
        self.title = child.find("title", ns).text
        self.date = child.find("date", ns).find("year", ns).text
        self.current_status = child.find("current-status", ns).text
        # Have to filter these to only contain RFCs.
        self.updates = [
            update.text
            for update in child.find("updates", ns) or []
            if update.text.startswith("RFC")
        ]
        self.updated_by = [
            updated.text
            for updated in child.find("updated-by", ns) or []
            if updated.text.startswith("RFC")
        ]
        self.obsoletes = [
            obsolete.text
            for obsolete in child.find("obsoletes", ns) or []
            if obsolete.text.startswith("RFC")
        ]
        self.obsoleted_by = [
            obsoleted.text
            for obsoleted in child.find("obsoleted-by", ns) or []
            if obsoleted.text.startswith("RFC")
        ]
        self.stream = child.find("stream", ns).text
        self.doi = child.find("doi", ns).text


def style_graph(a):
    for node in a.nodes():
        node.attr["URL"] = f"https://www.rfc-editor.org/info/{node.lower()}"
        match rfcs[node].current_status:
            case "INTERNET STANDARD":
                node.attr["shape"] = "box"
                node.attr["label"] = f"{node}\nSTD"
                node.attr["fillcolor"] = "darkorchid1"
                node.attr["style"] = "filled"
            case "DRAFT STANDARD":
                node.attr["shape"] = "doublecircle"
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


def print_graph(g):
    a = nx.nx_agraph.to_agraph(g)
    style_graph(a)
    a.write(sys.stdout)


def write_cyjs(g, filename):
    data = json_graph.cytoscape_data(g)
    with open(filename, "w") as f:
        json.dump(data, f)


def produce_svg(rfc_list, full):
    rfc_index = files("rfc_browser").joinpath("rfc-index.xml")
    tree = ET.parse(rfc_index)
    root = tree.getroot()

    for child in root.findall("rfc-entry", ns):
        rfc = RFC(child)
        rfcs[rfc.id] = rfc

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

    # Find the descendants of RFC1034 and RFC1035
    # Note that RFC1886 can be thrown into the mix.
    c = nx.compose(ubg, obg)
    l = []
    for r in rfc_list:
        x = nx.descendants(c, r)
        x.add(r)
        l.append(nx.subgraph(c, x))
    # Limit the graph to only those RFCs and their descendants
    g = nx.compose_all(l)

    # Write the full graph before any reductions
    if full:
        print_graph(g)
        return
    # write_cyjs(g, "before_reduction.cyjs")

    # Reduce the full graph into its transitive reduction
    t = nx.transitive_reduction(g)
    g_reduced = nx.intersection(g, t)
    print_graph(g_reduced)

    # Work hard to get rid of obsolete nodes. It should be a simple edge
    # contraction but it has certain complications I haven't quite yet
    # figured out, which means the code below isn't as simple as it could
    # be.  For example, 1886 gets disposed of even though we'd like to
    # keep it, as the user requested it as a root node.
    # h = g.reverse()
    # obg_restrict = nx.intersection(g, obg)
    # for u, v in obg_restrict.edges():
    #     try:
    #         nx.contracted_edge(h, (v, u), self_loops=False, copy=False)
    #     except:
    #         continue
    # h = h.reverse(copy=False)
    # h_noloop = h.copy()
    # for u, v in h.edges():
    #     if nx.has_path(g, v, u):
    #         h_noloop.remove_edge(u, v)
    # t = nx.transitive_reduction(h_noloop)
    # g_contracted = nx.intersection(h_noloop, t)
    # print_graph(g_contracted, "without_obsolete.gv")
