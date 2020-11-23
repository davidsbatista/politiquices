import json

from politiquices.webapp.webapp.app.sparql_queries import query_sparql, prefixes


def get_persons():
    query = """
        SELECT DISTINCT ?personLabel ?item ?image_url {
        ?item wdt:P31 wd:Q5 # get all human entities from the local graph
        SERVICE <https://query.wikidata.org/sparql> {
            OPTIONAL { ?item wdt:P18 ?image_url. }
            ?item rdfs:label ?personLabel
            SERVICE wikibase:label { 
                bd:serviceParam wikibase:language "pt". 
                ?item rdfs:label ?personLabel 
            }
      }
    }        """
    result = query_sparql(prefixes + "\n" + query, "local")
    persons = []
    for x in result["results"]["bindings"]:
        image_url = None
        if 'image_url' in x:
            image_url = x["image_url"]["value"]
        persons.append(
            {'wiki_id': x["item"]["value"].split("/")[-1],
             'name': x["personLabel"]["value"],
             'image_url': image_url,
            }
        )
    return persons


def main():
    data = get_persons()
    with open('persons.json', 'wt') as f_out:
        json.dump(data, f_out, indent=True, sort_keys='True')


if __name__ == '__main__':
    main()
