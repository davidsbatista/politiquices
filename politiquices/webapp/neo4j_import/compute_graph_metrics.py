import networkx as nx


def load_nodes():
    wiki_id2node_id = dict()
    nodes = []
    with open('nodes.csv') as f_in:
        for idx, line in enumerate(f_in):
            wiki_id, name = line.split(",")
            nodes.append((idx, {"name": name.strip(), "wiki_id": wiki_id}))
            wiki_id2node_id[wiki_id] = idx
    return nodes, wiki_id2node_id


def load_edges(wiki_id2node_id):
    edges = []
    with open('edges_opposes.csv') as f_in:
        for idx, line in enumerate(f_in):
            source, target, weight = line.split(",")
            edges.append(
                (wiki_id2node_id[source], wiki_id2node_id[target],
                 {'weight': int(weight), 'rel_type': 'opposes'})
            )
    with open('edges_supports.csv') as f_in:
        for idx, line in enumerate(f_in):
            source, target, weight = line.split(",")
            edges.append((wiki_id2node_id[source], wiki_id2node_id[target],
                          {'weight': int(weight), 'rel_type': 'supports'})
                         )
    return edges


def main():
    # read the data and load into the Graph
    nodes, wiki_id2node_id = load_nodes()
    edges = load_edges(wiki_id2node_id)
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # compute the metrics
    # see: https://networkx.org/documentation/stable/tutorial.html#analyzing-graphs
    for x in list(nx.connected_components(G)):
        print(x)

    # write output in neo4j CSV format


if __name__ == '__main__':
    main()
