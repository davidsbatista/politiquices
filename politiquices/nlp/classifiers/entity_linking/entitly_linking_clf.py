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
        # ToDo: remove dashes and ANSI version of a string
        pass

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
        Try to expand the 'entity', get all person named entities in the news text, and only keep
        those that overlap on at least one token with 'entity'.
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

    @staticmethod
    def fuzzy_match(entity, candidate, threshold=0.75):
        def fuzzy_compare(a, b):
            seq = difflib.SequenceMatcher(None, a, b)
            return seq.ratio()

        if fuzzy_compare(entity, candidate["label"]) >= threshold:
            return True

        if "aliases" in candidate and candidate["aliases"] is not None:
            for alias in candidate["aliases"]:
                if fuzzy_compare(entity, alias) >= threshold:
                    return True

        return False

    def entity_linking(self, entity, url):
        candidates = self.query_kb(entity, all_results=True)
        entity = self.mappings.get(entity, entity)
        no_wiki = jsonlines.open("no_wiki_id.jsonl", "a")

        # no candidates generated
        if len(candidates) == 0:
            no_wiki.write({"entity": entity, "expanded": "no_candidates", "url": url})
            return None

        # just one candidate
        if len(candidates) == 1:
            if self.fuzzy_match(entity, candidates[0]):
                return candidates[0]

        # several candidates: filter exact string matches only, and if only 1, return that one;
        if len(candidates) > 1:
            if len(full_match := self.exact_matches_only(entity.strip(), candidates)) == 1:
                return full_match[0]

        # try to expand the named-entity based on the article's text
        text = self.articles_db.get_article_full_text(url)
        expanded_entities = self.expand_ne(entity, text)

        # could not expand the named-entity
        if len(expanded_entities) == 0:
            self.log_results(candidates, entity, no_wiki, expanded_entities, url)

        # expanding process just returned one candidate
        if len(expanded_entities) == 1:

            # if it has an exact match with any previous gathered candidates
            expanded_entity = expanded_entities[0]
            if len(full_match_label := self.exact_matches_only(expanded_entity, candidates)) == 1:
                return full_match_label[0]

            # otherwise use the expanded entity to retrieve new candidates from the KB
            candidates = self.query_kb(expanded_entities[0], all_results=True)

            # if from all the newly retrieved candidates only one has an exact match with the
            # expanded entity, return that one
            if len(full_match := self.exact_matches_only(expanded_entity, candidates)) == 1:
                return full_match[0]

            # if there's only one and soft string matching occurs return that one
            if len(candidates) == 1 and self.fuzzy_match(expanded_entities[0], candidates[0]):
                return candidates[0]

            self.log_results(candidates, entity, no_wiki, expanded_entities, url)
            return None

        # if there's more than one expanded entity
        if len(expanded_entities) > 1:
            exact_matches = []
            for entity in expanded_entities:
                exact_matches.extend(self.exact_matches_only(entity, candidates))
            if len(exact_matches) == 1:
                return exact_matches[0]

            self.log_results(candidates, entity, no_wiki, expanded_entities, url)

            return None
