import re
import difflib
from functools import lru_cache

import textdistance
from elasticsearch import Elasticsearch
from jsonlines import jsonlines


class EntityLinking:

    def __init__(self, ner, articles_db, mappings):
        self.elastic_search = self._setup_es()
        self.ner = ner
        self.articles_db = articles_db
        self.mappings = mappings

    @staticmethod
    def log_results(candidates, entity, no_wiki, text_entities, url):
        no_wiki.write({
            "entity": entity,
            "expanded": text_entities,
            "candidates": candidates,
            "url": url,
        })

    @staticmethod
    def _setup_es():
        try:
            print("Setting up connection with ElasticSearch")
            es = Elasticsearch([{"host": "localhost", "port": 9200}])
            return es
        except Exception as e:
            raise Exception(f"Could not connect to ElasticSearch: {e}")

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def deburr_entity():
        pass
        # ToDo:
        # without dashes and ANSI version of a string

    @staticmethod
    def merge_substrings(entities):
        """
        This function eliminates entities which are already substrings of other entities.

        e.g.:
            input:['Ana Lourenço', 'Ana Dias Lourenço', 'Ana Afonso Dias Lourenço']
            output: ['Ana Afonso Dias Lourenço']

        Based on the principle that if a polysemous word appears two or more times in a
        written discourse, it is extremely likely that they will all share the same sense.
        (see: https://www.aclweb.org/anthology/H92-1045.pdf)
        """

        new_entities = []

        # sort the locations by size
        entities_sorted = sorted([EntityLinking.clean_entity(x) for x in entities], key=len)

        # starting with the shortest one see if it's a substring of any of the longer ones
        for idx, x in enumerate(entities_sorted):
            found = False
            for other in entities_sorted[idx + 1:]:
                if x in other or textdistance.levenshtein(x, other) <= 3:
                    found = True
                    break
            if not found and x not in new_entities:
                new_entities.append(x)

        return new_entities

    @lru_cache(maxsize=2000)
    def query_kb(self, entity, all_results=False):

        sanitized = ""
        for character in entity:
            if self.needs_escaping(character):
                sanitized += "\\%s" % character
            else:
                sanitized += character

        if self.mappings:
            entity_clean = self.mappings.get(sanitized, sanitized)
        else:
            entity_clean = sanitized

        entity_query = " AND ".join([token.strip() for token in entity_clean.split()])
        res = self.elastic_search.search(
            index="politicians",
            body={"query": {"query_string": {"query": entity_query}}}
        )

        if res["hits"]["hits"]:
            if all_results:
                return [r["_source"] for r in res["hits"]["hits"]]
            return res["hits"]["hits"][0]["_source"]

        if all_results:
            return []

        return {}

    def expand_ne(self, entity, text):
        """
        Try to expand the 'entity', get all the named entities in the text, and only keep those
        that overlap on some strings with 'entity'.
        """

        if not text:
            return []

        persons = self.ner.tag(text)
        expanded = [p for p in persons if entity in p and entity != p]
        expanded_clean = [self.clean_entity(x) for x in expanded]
        return self.merge_substrings(expanded_clean)

    @staticmethod
    def exact_matches_only(entity, candidates):
        """Keep only candidates whose label or aliases has an exact match with the entity"""
        matches = []
        for c in candidates:
            if entity.lower() == c["label"].lower():
                matches.append(c)
            elif "aliases" in c and c["aliases"] is not None:
                for alias in c["aliases"]:
                    if entity.lower() == alias.lower():
                        return [c]
        return matches

    def disambiguate(self, expanded_entities, candidates):

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
                matched += len(self.exact_matches_only(ent, [candidate]))
            return matched == len(entities)

        matching_candidates = [c for c in candidates if full_match_candidate(expanded_entities, c)]

        return matching_candidates

    @staticmethod
    def fuzzy_match(entity, candidate, threshold=0.77):
        def fuzzy_compare(a, b):
            seq = difflib.SequenceMatcher(None, a, b)
            return seq.ratio()

        if fuzzy_compare(entity, candidate["label"]) > threshold:
            return True

        if "aliases" in candidate and candidate["aliases"] is not None:
            for alias in candidate["aliases"]:
                if fuzzy_compare(entity, alias) > threshold:
                    return True

        return False

    def entity_linking(self, entity, url):
        candidates = self.query_kb(entity, all_results=True)
        no_wiki = jsonlines.open("no_wiki_id.jsonl", "a")

        # no candidates generated
        if len(candidates) == 0:
            # print("No candidates from KB -> ", entity)
            no_wiki.write({"entity": entity, "expanded": "no_candidates", "url": url})
            return None

        # just one candidate
        if len(candidates) == 1:
            return candidates[0]

        # more than one, filter for full string match, and return if only 1
        if len(candidates) > 1:
            if len(full_match := self.exact_matches_only(entity.strip(), candidates)) == 1:
                return full_match[0]

        # try to expand the named-entity based on the article's text
        text = self.articles_db.get_article_full_text(url)
        text_entities = self.expand_ne(entity, text)

        # could not expand the named-entity
        if len(text_entities) == 0:
            self.log_results(candidates, entity, no_wiki, text_entities, url)
            # print("case 2 -> ", entity, url, len(candidates), text_entities, len(text_entities))
            """
            for e in candidates:
                print(e)
            print()
            """

        # expanding process just returned one candidate
        if len(text_entities) == 1:
            expanded_entity = text_entities[0]

            # if it has an exact match with any previous gathered candidates
            if full_match_label := self.exact_matches_only(expanded_entity, candidates) == 1:
                return full_match_label[0]

            # otherwise use the expanded entity to retrieve new candidates from the KB
            candidates = self.query_kb(text_entities[0], all_results=True)

            # no new candidates retrieved
            if len(candidates) == 0:
                self.log_results(candidates, entity, no_wiki, text_entities, url)
                print("case 3 -> ", entity, url, text_entities, len(text_entities))
                for e in candidates:
                    print(e)
                print()
                return None

            # if from all the newly retrieved candidates only one has an exact match with the
            # expanded entity, return that one
            full_match_label = self.exact_matches_only(expanded_entity, candidates)
            if len(full_match_label) == 1:
                return full_match_label[0]

            # if there's only one and soft string matching occurs return that one
            if len(candidates) == 1:
                if self.fuzzy_match(text_entities[0], candidates[0]):
                    return candidates[0]

            self.log_results(candidates, entity, no_wiki, text_entities, url)
            """
            print("case 4 -> ", entity, text_entities, len(text_entities))
            for e in candidates:
                print(e)
            print()
            """
            return None

        # if there's more than one expanded entity
        if len(text_entities) > 1:
            matches = self.disambiguate(text_entities, candidates)
            if len(matches) == 1:
                return matches[0]
            """
            print("\n" + url)
            print(entity)
            print("case 5 -> ", entity, text_entities, len(text_entities))
            for e in candidates:
                print(e)
            print()
            """
            self.log_results(candidates, entity, no_wiki, text_entities, url)
            return None
