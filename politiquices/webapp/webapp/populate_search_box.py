"""
JSON file used to populate the search box politiquices.pt
Move the generated 'persons.json' file into 'webapp/app/static'
"""
import json

from politiquices.webapp.webapp.app.sparql_queries import query_sparql, prefixes

wikidata_endpoint = "http://0.0.0.0:3030/wikidata/query"


def get_persons():
    query = f"""
        SELECT DISTINCT ?personLabel ?item ?image_url {{
            ?item wdt:P31 wd:Q5 # get all human entities from the local graph
            SERVICE <{wikidata_endpoint}> {{
                OPTIONAL {{ ?item wdt:P18 ?image_url. }}
                ?item rdfs:label ?personLabel FILTER(LANG(?personLabel)="pt") .
            }}
        }}
    """
    result = query_sparql(prefixes + "\n" + query, "politiquices")
    persons = []
    seen = set()

    for x in result["results"]["bindings"]:
        wikid_id = x["item"]["value"].split("/")[-1]
        if wikid_id in seen:
            continue

        image_url = None

        if "image_url" in x:
            image_url = x["image_url"]["value"]

        persons.append(
            {
                "wiki_id": wikid_id,
                "name": x["personLabel"]["value"],
                "image_url": image_url,
            }
        )
        seen.add(x["item"]["value"].split("/")[-1])

    return persons


def main():
    data = get_persons()
    with open("persons.json", "wt") as f_out:
        json.dump(data, f_out, indent=True, sort_keys="True")


if __name__ == "__main__":
    main()
