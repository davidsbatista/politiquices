import networkx as nx
from networkx.algorithms.community.centrality import girvan_newman
from networkx.algorithms.link_analysis.pagerank_alg import pagerank
from networkx.algorithms.community import k_clique_communities

node_info = dict()


class Node:
    def __init__(self, nx_id, name, wiki_id):
        self.nx_id = nx_id
        self.name = name
        self.wiki_id = wiki_id

    def to_nx_format(self):
        return self.nx_id, {"name": self.name, "wiki_id": self.wiki_id}

    def to_neo4j_format(self):
        return self.wiki_id, self.name


class Edge:
    def __init__(self, source, target, weight, rel_type):
        self.source = source
        self.target = target
        self.weight = weight
        self.rel_type = rel_type


def load_nodes():
    wiki_id2node_id = dict()
    nxid2wiki_id = dict()
    nodes = []
    with open('nodes.csv') as f_in:
        for idx, line in enumerate(f_in):
            wiki_id, name = line.split(",")
            nodes.append((idx, {"name": name.strip(), "wiki_id": wiki_id}))
            node_info[wiki_id] = {"name": name.strip(), "wiki_id": wiki_id}
            wiki_id2node_id[wiki_id] = idx
            nxid2wiki_id[idx] = wiki_id
    return nodes, wiki_id2node_id, nxid2wiki_id


def load_edges(wiki_id2node_id):
    edges_opposes = []
    edges_supports = []

    with open('edges_opposes.csv') as f_in:
        for idx, line in enumerate(f_in):
            source, target, weight = line.split(",")
            edges_opposes.append(
                (wiki_id2node_id[source], wiki_id2node_id[target],
                 {'weight': int(weight), 'rel_type': 'opposes'})
            )

    with open('edges_supports.csv') as f_in:
        for idx, line in enumerate(f_in):
            source, target, weight = line.split(",")
            edges_supports.append((wiki_id2node_id[source], wiki_id2node_id[target],
                                   {'weight': int(weight), 'rel_type': 'supports'})
                                  )

    return edges_opposes, edges_supports


def main():
    # read the data and load into the Graph
    nodes, wiki_id2node_id, nxid2wiki_id = load_nodes()
    edges_opposes, edges_supports = load_edges(wiki_id2node_id)
    g = nx.Graph()
    # g.add_nodes_from(edges_opposes)
    g.add_edges_from(edges_supports)

    # compute the metrics
    # see: https://networkx.org/documentation/stable/tutorial.html#analyzing-graphs
    # for x in list(nx.connected_components(g)):
    #     print(x)

    page_rank_values = pagerank(g)

    communities = list(k_clique_communities(g, 4))
    for c in communities:
        for n in c:
            print(n, node_info[nxid2wiki_id[n]])
        print("\n-----------")

    exit(-1)

    # write output in neo4j CSV format
    with open("nodes_page_rank.csv", "w") as f_out:
        for k, v in page_rank_values.items():
            wiki_id = nxid2wiki_id[k]
            name = node_info[wiki_id]['name']
            print(wiki_id, name, v)
            f_out.write(f"{wiki_id},{name},{v}" + "\n")


if __name__ == '__main__':
    main()
