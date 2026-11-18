"""Export a LemonGraph transaction's view of the graph to NetworkX.

    import LemonGraph
    from LemonGraph.nx import to_networkx

    with LemonGraph.Graph(path) as g:
        with g.transaction(write=False) as txn:
            G = to_networkx(txn)

NetworkX is not a LemonGraph dependency - it is imported on first use.

Nodes are keyed by LemonGraph node ID and carry 'type', 'value' and all node
properties as attributes. Edges are keyed by LemonGraph edge ID (so the
default MultiDiGraph keeps parallel edges) and carry 'type', 'value' and all
edge properties. Graph-level properties land in G.graph.
"""

from __future__ import absolute_import


def _attrs(obj, skip):
    return dict((k, v) for k, v in obj.as_dict().items() if k not in skip)


def to_networkx(txn, graph_class=None, node_type=None, edge_type=None, beforeID=None):
    """Return a NetworkX graph of the nodes/edges visible to txn.

    graph_class: NetworkX class to instantiate (default nx.MultiDiGraph). With
                 a non-multi class, parallel edges between the same pair of
                 nodes collapse to the last one seen.
    node_type:   only export nodes of this type (edges are then restricted to
                 those whose endpoints were both exported)
    edge_type:   only export edges of this type
    beforeID:    historical view - export the graph as of this log position
    """
    import networkx as nx

    if graph_class is None:
        graph_class = nx.MultiDiGraph
    G = graph_class()
    G.graph.update(txn.as_dict())

    kw = {} if beforeID is None else {'beforeID': beforeID}
    if node_type is not None:
        kw['type'] = node_type
    for node in txn.nodes(**kw):
        G.add_node(node.ID, **_attrs(node, ('ID',)))

    kw = {} if beforeID is None else {'beforeID': beforeID}
    if edge_type is not None:
        kw['type'] = edge_type
    multi = G.is_multigraph()
    for edge in txn.edges(**kw):
        if edge.srcID not in G or edge.tgtID not in G:
            continue
        attrs = _attrs(edge, ('ID', 'srcID', 'tgtID'))
        if multi:
            G.add_edge(edge.srcID, edge.tgtID, key=edge.ID, **attrs)
        else:
            G.add_edge(edge.srcID, edge.tgtID, ID=edge.ID, **attrs)
    return G
