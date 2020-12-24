from functools import lru_cache

from elasticsearch import Elasticsearch

print("Setting up connection with Elasticsearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])


@lru_cache(maxsize=2000)
def entity_linking(entity, all_results=False):

    def needs_escaping(char):
        escape_chars = {
            "\\": True,
            "+": True,
            "-": True,
            "!": True,
            "(": True,
            ")": True,
            ":": True,
            "^": True,
            "[": True,
            "]": True,
            '"': True,
            "{": True,
            "}": True,
            "~": True,
            "*": True,
            "?": True,
            "|": True,
            "&": True,
            "/": True,
        }
        return escape_chars.get(char, False)

    mappings = {
        "Carrilho": "Manuel Maria Carrilho",
        "Costa": "António Costa",
        "Durão": "Durão Barroso",
        "Ferreira de o Amaral": "Joaquim Ferreira do Amaral",
        "Jerónimo": "Jerónimo de Sousa",
        "Marcelo": "Marcelo Rebelo de Sousa",
        "Marques Mendes": "Luís Marques Mendes",
        "Menezes": "Luís Filipe Menezes",
        "Moura Guedes": "Manuela Moura Guedes",
        "Nobre": "Fernando Nobre",
        "Portas": "Paulo Portas",
        "Rebelo de Sousa": "Marcelo Rebelo de Sousa",
        "Relvas": "Miguel Relvas",
        "Santana": "Pedro Santana Lopes",
        "Santos Silva": "Augusto Santos Silva",
        "Soares": "Mário Soares",
        "Sousa Tavares": "Miguel Sousa Tavares",
    }

    sanitized = ""
    for character in entity:
        if needs_escaping(character):
            sanitized += "\\%s" % character
        else:
            sanitized += character

    entity_clean = mappings.get(sanitized, sanitized)
    entity_query = " AND ".join([token.strip() for token in entity_clean.split()])
    res = es.search(index="politicians", body={"query": {"query_string": {"query": entity_query}}})

    if res["hits"]["hits"]:
        if all_results:
            return [r['_source'] for r in res["hits"]["hits"]]
        # print('entity_query: ', entity_query, ' -> ', res["hits"]["hits"][0]["_source"])
        return res["hits"]["hits"][0]["_source"]

    if all_results:
        return []

    # print('entity_query: ', entity_query, ' -> ', None)
    return {}
