import re
import difflib
from functools import lru_cache

from elasticsearch import Elasticsearch

print("Setting up connection with ElasticSearch")
es = Elasticsearch([{"host": "localhost", "port": 9200}])


@lru_cache(maxsize=2000)
def query_kb(entity, all_results=False):

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
        "António Costa": "António Luís Santos da Costa",
        "Costa": "António Luís Santos da Costa",

        "Carrilho": "Manuel Maria Carrilho",

        "Cavaco Silva": 'Aníbal Cavaco Silva',
        "Cavaco": 'Aníbal Cavaco Silva',

        "Durão": "Durão Barroso",
        "Ferreira de o Amaral": "Joaquim Ferreira do Amaral",
        "Jerónimo": "Jerónimo de Sousa",
        'José Pedro Aguiar-Branco': 'José Pedro Aguiar Branco',

        "Louçã": "Francisco Louçã",
        "Louça": "Francisco Louçã",

        "Marcelo": "Marcelo Rebelo de Sousa",
        "Rebelo de Sousa": "Marcelo Rebelo de Sousa",

        "Marques Mendes": "Luís Marques Mendes",
        "Menezes": "Luís Filipe Menezes",
        "Moura Guedes": "Manuela Moura Guedes",
        "Nobre": "Fernando Nobre",
        "Passos": "Pedro Passos Coelho",
        "Portas": "Paulo Portas",
        "Relvas": "Miguel Relvas",
        "Santana": "Pedro Santana Lopes",
        "Santos Silva": "Augusto Santos Silva",
        "Soares": "Mário Soares",
        "Sousa Tavares": "Miguel Sousa Tavares",

        "Vieira da Silva": "José Vieira da Silva",
        "Vitor Gaspar": "Vítor Gaspar"
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


def clean_entity(entity):
    rep = {
        "Sr.": "",
        "[": "",
        "”": "",
        "doutor": "",
        "dr.": "",
        "Dr.": "",
        "sr.": "",
        "Foto": "",
        "Parabéns": "",
    }

    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    new_entity = pattern.sub(lambda m: rep[re.escape(m.group(0))], entity)

    return new_entity.strip()


def deburr_entity():
    pass
    # ToDo:
    # without dashes and ANSI version of a string


def expand_entities(entity, text, rule_ner):
    all_entities, persons = rule_ner.tag(text)
    expanded = [p for p in persons if entity in p and entity != p]
    expanded_clean = [clean_entity(x) for x in expanded]
    return merge_substrings(expanded_clean)


def find_perfect_match(entity, candidates):

    # filter only for those whose label or aliases are a perfect match
    matches = []
    for c in candidates:
        if entity == c['label']:
            return [c]
        else:
            if 'aliases' in c and c['aliases'] is not None:
                for alias in c['aliases']:
                    if entity.lower() == alias.lower():
                        return [c]
    return matches


def merge_substrings(entities):
    """
    This function eliminates entities which are already substrings of other  entities.

    This is based on the principle that if a polysemous word appears two or more times in a
    written discourse, it is extremely likely that they will all share the same sense.
    (see: https://www.aclweb.org/anthology/H92-1045.pdf)
    """

    # ToDo:
    # result = merge_substrings(['Jaime Gama', 'Jaime de Gama'])
    # assert result == ['Jaime Gama']

    # result = merge_substrings(['Paulo Azevedo', 'Paulo de Azevedo'])
    # assert result == ['Paulo de Azevedo']

    # result = merge_substrings(['Jose da Silva Lopes', 'José da Silva Lopes'])
    # assert result == ['José da Silva Lopes']

    # result = merge_substrings(["Guilherme d'Oliveira Martins", "Guilherme d' Oliveira Martins"])
    # assert result == ['Guilherme d'Oliveira Martins']

    # ['Ana Lourenço', 'Ana Dias Lourenço', 'Ana Afonso Dias Lourenço']
    # ['Ana Afonso Dias Lourenço']

    # ['Luís Filipe Menezes', 'Luis Filipe Menezes']
    # ['Luís Filipe Menezes']

    new_entities = []

    # sort the locations by size
    entities_sorted = sorted([clean_entity(x) for x in entities], key=len)

    # starting with the shortest one see if it's a substring of any of the longer ones
    for idx, x in enumerate(entities_sorted):
        found = False
        for other in entities_sorted[idx + 1:]:
            if x in other:  # ToDo: use a more relaxed/fuzzy matching here
                found = True
                break
        if not found and x not in new_entities:
            new_entities.append(x)

    return new_entities


def disambiguate(expanded_entities, candidates):

    """
    # ToDo:
    - several expanded entities
    - if more than 'threshold' of expanded entities match full with a candiadate return that
      candidate

    case 3 ->  ['Joe Berardo', 'José Berardo'] 2
    {'wiki': 'Q3186200', 'label': 'José Manuel Rodrigues Berardo', 'aliases': ['Joe Berardo',
    'Joe berardo', 'José berardo', 'José Berardo', 'José manuel rodrigues berardo',
    'Colecção Berardo']}

    case 3 ->  ['Joe Berardo', 'José Berardo', 'Coleção Berardo', 'Berardo um Acordo Quadro',
    'José Manuel Rodrigues Berardo']

    case 3 ->  ['Luis Filipe Menezes', 'Luís Filipe Menezes']
    {'wiki': 'Q6706787', 'last_modified': '2020-12-01T22:53:40Z', 'label': 'Luís Filipe Menezes', 'aliases': ['Luís Filipe Meneses', 'Luis Filipe de Menezes', 'Luís Filipe de Menezes']}
    {'wiki': 'Q10321558', 'last_modified': '2020-12-24T01:32:58Z', 'label': 'Luís Menezes', 'aliases': ['Luís de Menezes', 'Luís Filipe Valenzuela Tavares de Menezes Lopes']}

    Nogueira Pinto
    case 3 ->  ['Maria Nogueira Pinto', 'Maria José Nogueira Pinto'] 2
    {'wiki': 'Q6123866', 'last_modified': '2020-12-19T15:30:57Z', 'label': 'Jaime Nogueira Pinto', 'aliases': ['Jaime nogueira pinto', 'Jaime Alexandre Nogueira Pinto']}
    {'wiki': 'Q10325930', 'last_modified': '2020-12-24T02:17:41Z', 'label': 'Maria José Nogueira Pinto', 'aliases': ['Maria José Pinto da Cunha Avilez Nogueira Pinto']}

    Gaspar
    case 3 ->  ['Víto Gaspar', 'Vítor Gaspar'] 2
    {'wiki': 'Q2118027', 'last_modified': '2020-12-26T03:22:53Z', 'label': 'Vítor Gaspar', 'aliases': ['Vitor Louçã Rabaça Gaspar', 'Vitor Gaspar']}
    {'wiki': 'Q66984570', 'last_modified': '2020-06-10T10:01:41Z', 'label': 'Emanuel Gaspar', 'aliases': ['Emanuel Gaspar de Freitas']}
    {'wiki': 'Q27093786', 'last_modified': '2020-12-24T07:28:37Z', 'label': 'Luís Gaspar da Silva', 'aliases': None}
    {'wiki': 'Q24691796', 'last_modified': '2020-12-24T07:13:35Z', 'label': 'António Silva Henriques Gaspar', 'aliases': None}


    - just one expanded entity but two candidates
    case 2 ->  ['Filipe Menezes']
    {'wiki': 'Q6706787', 'last_modified': '2020-12-01T22:53:40Z', 'label': 'Luís Filipe Menezes',
    aliases': ['Luís Filipe Meneses', 'Luis Filipe de Menezes', 'Luís Filipe de Menezes']}
    {'wiki': 'Q10321558', 'last_modified': '2020-02-05T21:22:25Z', 'label': 'Luís Menezes',
    'aliases': ['Luís de Menezes', 'Luís Filipe Valenzuela Tavares de Menezes Lopes']}
    """

    def full_match_candidate(entities, candidate):
        matched = 0
        for ent in expanded_entities:
            matched += len(find_perfect_match(ent, [candidate]))
        return matched == len(entities)

    matching_candidates = [c for c in candidates if full_match_candidate(expanded_entities, c)]

    return matching_candidates


def fuzzy_match(entity, candidate, threshold=0.77):

    def fuzzy_compare(a, b):
        seq = difflib.SequenceMatcher(None, a, b)
        return seq.ratio()

    if fuzzy_compare(entity, candidate['label']) > threshold:
        return True

    if 'aliases' in candidate and candidate['aliases'] is not None:
        for alias in candidate['aliases']:
            if fuzzy_compare(entity, alias) > threshold:
                return True

    return False
