import os
import re

from elasticsearch import Elasticsearch
from spacy.pipeline import EntityRuler

import pt_core_news_lg

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


class RuleBasedNer:

    def __init__(self):
        self.entities_file = os.path.join(APP_ROOT, "PER_entities.txt")
        self.connectors = ['do', 'da', 'de', 'dos']
        self.file_names = self._get_names_file(self.entities_file)
        self.kb_names = self._get_names_kb()
        self.patterns = self.build_token_patterns()
        self.ner = self.build_ner()

    @staticmethod
    def _get_names_kb():
        es = Elasticsearch([{"host": "localhost", "port": 9200}])
        res = es.search(index="politicians",
                        body={"query": {"match_all": {}},
                              "size": 2000})

        for r in res['hits']['hits']:
            if r['_source']['label'] is None:
                print(r)

        all_names = sorted([r['_source']['label'] for r in res['hits']['hits']],
                           key=lambda x: len(x),
                           reverse=True)

        return all_names

    @staticmethod
    def _get_names_file(fname):
        with open(fname, 'rt') as f_in:
            names = {line.strip() for line in f_in if len(line) > 1}
        return list(names)

    @staticmethod
    def dict_entry(name):
        for token in name.split():
            yield {"TEXT": token}

    def build_token_patterns(self):
        names = set()
        patterns = []

        for name in self.kb_names:
            name_clean = re.sub(r'\(.*\)', '', name)  # remove text inside parenthesis
            name_clean = re.sub(r'(,.*)', ' ', name_clean)  # remove comma and all text after
            name_parts = name_clean.split()
            names.add(name_clean)

            # exactly as it is
            p = {"label": "PER", "pattern": list(self.dict_entry(name))}
            patterns.append(p)

            # first and last name
            if len(name_parts) > 2:
                name = name_parts[0] + ' ' + name_parts[-1]
                names.add(name)
                p = {"label": "PER", "pattern": list(self.dict_entry(name))}
                patterns.append(p)

        # add some hand picked examples
        for name in self.file_names:
            names.add(name)
            p = {"label": "PER", "pattern": list(self.dict_entry(name))}
            patterns.append(p)

        with open('kb_names_patterns.txt', 'wt') as f_out:
            for p in patterns:
                f_out.write(str(p['pattern']) + '\n')

        return patterns

    def build_ner(self):
        # load spaCy PT (large) model and disable part-of-speech tagging and syntactic parsing
        nlp = pt_core_news_lg.load(disable=["tagger", "parser"])
        config = {
            "phrase_matcher_attr": None,
            "validate": True,
            "overwrite_ents": False,
            "ent_id_sep": "||",
        }
        entity_ruler = nlp.add_pipe("entity_ruler", config=config)

        # hard code some entities, note this are phrase patterns
        self.patterns.append({'label': 'PER', 'pattern': 'Marinho e Pinto'})
        self.patterns.append({'label': 'PER', 'pattern': 'Ribeiro e Castro'})

        # entity_ruler.initalize()
        entity_ruler.initialize(lambda: [], nlp=nlp, patterns=self.patterns)

        # add rule-based Entity Recognizer which don't overwrites entities recognized by the model
        # ruler_person_entities = EntityRuler(nlp, overwrite_ents=False)
        # ruler_person_entities.add_patterns(self.patterns)
        # ruler_person_entities.name = 'person_entities'

        # runs before the ner
        # nlp.add_pipe(ruler_person_entities, before="ner", name='person_entities')
        # nlp.add_pipe('person_entities', before="ner")

        return nlp

    def tag(self, title, all_entities=False):

        if self.ner is None:
            print("NER not initialized")
            return None

        doc = self.ner(title)
        entities = {ent.text: ent.label_ for ent in doc.ents}
        persons = []

        for k, v in entities.items():
            if v == "PER":
                persons.append(k)

        if all_entities:
            return entities, persons

        return None, persons
