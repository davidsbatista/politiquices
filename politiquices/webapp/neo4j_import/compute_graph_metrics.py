import json
from collections import defaultdict

import networkx as nx
from networkx.algorithms.link_analysis.pagerank_alg import pagerank

from politiquices.webapp.webapp.utils.sparql_queries import get_graph_links

node_info = dict()


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


def get_graph_from_sparql():
    links = get_graph_links()
    nodes = defaultdict(dict)
    edge_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    with open("../webapp/app/static/json/wiki_id_info.json") as f_in:
        wiki_id_info = json.load(f_in)

    all_edges_supports = open('all_edges_supports_urls.csv', 'w')
    all_edges_opposes = open('all_edges_opposes_urls.csv', 'w')

    print(len(links))

    for x in links:
        wiki_id_a = x["person_a"].split("/")[-1]
        wiki_id_b = x["person_b"].split("/")[-1]
        name_a = wiki_id_info[wiki_id_a]["name"]
        name_b = wiki_id_info[wiki_id_b]["name"]

        # build nodes
        if wiki_id_a not in nodes:
            nodes[wiki_id_a] = name_a

        if wiki_id_b not in nodes:
            nodes[wiki_id_b] = name_b

        rel = 'ACUSA' if "opposes" in x['rel_type'] else 'APOIA'

        # add direction and nodes
        if x["rel_type"].startswith("ent1"):
            edge_counts[wiki_id_a][wiki_id_b][x["rel_type"]] += 1
            if rel == "ACUSA" in rel:
                all_edges_opposes.write(f"{wiki_id_a},{wiki_id_b},{x['date']},{x['url']}"+"\n")
            else:
                all_edges_supports.write(f"{wiki_id_b},{wiki_id_a},{x['date']},{x['url']}" + "\n")

        elif x["rel_type"].startswith("ent2"):
            edge_counts[wiki_id_b][wiki_id_a][x["rel_type"]] += 1
            if rel == "ACUSA" in rel:
                all_edges_opposes.write(f"{wiki_id_a},{wiki_id_b},{x['date']},{x['url']}"+"\n")
            else:
                all_edges_supports.write(f"{wiki_id_b},{wiki_id_a},{x['date']},{x['url']}" + "\n")

    with open("nodes.csv", "w") as f_out:
        for k, v in nodes.items():
            f_out.write(f"{k},{v}" + "\n")

    f_out_opposes = open("edges_opposes.csv", "w")
    f_out_supports = open("edges_supports.csv", "w")

    for start_node, end_nodes in edge_counts.items():
        for end_node, rels in end_nodes.items():
            for rel_type, freq in rels.items():
                if "opposes" in rel_type:
                    f_out_opposes.write(f"{str(start_node)},{str(end_node)},{str(freq)}" + "\n")

                if "supports" in rel_type:
                    f_out_supports.write(f"{str(start_node)},{str(end_node)},{str(freq)}" + "\n")

    f_out_opposes.close()
    f_out_supports.close()


def main():
    print("Querying SPARQL..")
    get_graph_from_sparql()

    print("Computing metrics..")
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
    """
    communities = list(k_clique_communities(g, 4))
    for c in communities:
        for n in c:
            print(n, node_info[nxid2wiki_id[n]])
        print("\n-----------")
    """

    # write output in neo4j CSV format
    with open("nodes_page_rank.csv", "w") as f_out:
        for k, v in page_rank_values.items():
            wiki_id = nxid2wiki_id[k]
            name = node_info[wiki_id]['name']
            f_out.write(f"{wiki_id},{name},{v}" + "\n")


if __name__ == '__main__':
    main()
