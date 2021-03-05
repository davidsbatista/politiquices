import json
from collections import defaultdict
from politiquices.webapp.webapp.lib.sparql_queries import get_graph_links

node_info = dict()


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
                all_edges_opposes.write(f"{wiki_id_a},{wiki_id_b},{x['date']},{x['url']}" + "\n")
            else:
                all_edges_supports.write(f"{wiki_id_a},{wiki_id_b},{x['date']},{x['url']}" + "\n")

        elif x["rel_type"].startswith("ent2"):
            edge_counts[wiki_id_b][wiki_id_a][x["rel_type"]] += 1
            if rel == "ACUSA" in rel:
                all_edges_opposes.write(f"{wiki_id_b},{wiki_id_a},{x['date']},{x['url']}"+"\n")
            else:
                all_edges_supports.write(f"{wiki_id_b},{wiki_id_a},{x['date']},{x['url']}" + "\n")

    with open("nodes.csv", "w") as f_out:
        for k, v in nodes.items():
            f_out.write(f"{k},{v}" + "\n")


def main():
    print("Querying SPARQL...")
    get_graph_from_sparql()


if __name__ == '__main__':
    main()
