"""
JSON file used to populate the search box politiquices.pt
Move the generated 'persons.json' file into 'webapp/app/static'
"""
import json

from politiquices.webapp.webapp.app.sparql_queries import query_sparql, prefixes


def get_persons():
    persons_query = """
        SELECT DISTINCT ?personLabel ?item ?image_url {
            ?item wdt:P31 wd:Q5 # get all human entities from the local graph
            SERVICE <http://0.0.0.0:3030/wikidata/query> {
                OPTIONAL { ?item wdt:P18 ?image_url. }
                ?item rdfs:label ?personLabel FILTER(LANG(?personLabel)="pt") .
            }
        }
        ORDER BY ?personLabel
        """

    result = query_sparql(prefixes + "\n" + persons_query, "politiquices")
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


def get_parties():
    parties_query = """
    SELECT DISTINCT ?political_party ?party_label ?party_logo (COUNT(?person) as ?nr_personalities) 
    {
        ?person wdt:P31 wd:Q5 .
        SERVICE <http://0.0.0.0:3030/wikidata/query> {
            ?person wdt:P102 ?political_party .
            ?political_party rdfs:label ?party_label .
            OPTIONAL {?political_party wdt:P154 ?party_logo. }
            FILTER(LANG(?party_label) = "pt")
      }
    } 
    GROUP BY ?political_party ?party_label ?party_logo
    HAVING (COUNT(?person) > 2)
    ORDER BY DESC(?nr_personalities)
    """

    result = query_sparql(prefixes + "\n" + parties_query, "politiquices")
    persons = []
    seen = set()
    for x in result["results"]["bindings"]:

        wikid_id = x["political_party"]["value"].split("/")[-1]
        if wikid_id in seen:
            continue

        image_url = None

        if "party_logo" in x:
            image_url = x["party_logo"]["value"]

        persons.append(
            {
                "wiki_id": wikid_id,
                "name": x["party_label"]["value"],
                "image_url": image_url,
            }
        )
        seen.add(x["political_party"]["value"].split("/")[-1])

    return persons


def main():
    data = get_persons()
    print(f'{len(data)} persons found')
    with open("persons.json", "wt") as f_out:
        json.dump(data, f_out, indent=True, sort_keys="True")

    data = get_parties()
    print(f'{len(data)} parties found')
    with open("parties.json", "wt") as f_out:
        json.dump(data, f_out, indent=True, sort_keys="True")


if __name__ == "__main__":
    main()
