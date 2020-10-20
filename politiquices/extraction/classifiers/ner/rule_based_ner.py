import os
import re

from elasticsearch import Elasticsearch
from spacy.pipeline import EntityRuler

import pt_core_news_sm

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

"""
patterns = [
    {"label": "PER", "pattern": [{"TEXT": "Durão"}, {"TEXT": "Barroso"}], "id": "Q1232"},
    {"label": "PER", "pattern": [{"TEXT": "Durão"}], "id": "Q1232"},
    {"label": "PER", "pattern": [{"TEXT": "Barroso"}], "id": "Q1232"},
]
"""


class RuleBasedNer:
    def __init__(self):
        self.entities_file = os.path.join(APP_ROOT, "PER_entities.txt")
        self.connectors = ['do', 'da', 'de', 'dos']
        self.file_names = self._get_names_file(self.entities_file)
        self.kb_names = self._get_names_kb()
        self.patterns = self.build_patterns()
        self.ner = self.build_ner()

    @staticmethod
    def _get_names_kb():
        es = Elasticsearch([{"host": "localhost", "port": 9200}])
        res = es.search(index="politicians",
                        body={"query": {"match_all": {}},
                              "size": 2000})
        all_names = sorted([r['_source']['label'] for r in res['hits']['hits']])

        """
        with open('kb_names.txt', 'wt') as f_out:
            for name in sorted(all_names):
                f_out.write(name+'\n')
        """

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

    def build_patterns(self):
        names = set()
        patterns = []

        for name in self.kb_names:
            name_clean = re.sub(r'\(.*\)', '', name)  # remove text inside parenthesis
            name_clean = re.sub(r'(,.*)', ' ', name_clean)  # remove comma and all text after
            name_parts = name_clean.split()
            names.add(name_clean)

            # first and last name
            if len(name_parts) > 2:
                name = name_parts[0] + ' ' + name_parts[-1]
                names.add(name)
                p = {"label": "PER", "pattern": list(self.dict_entry(name))}
                patterns.append(p)

            # skip second name
            if len(name_parts) > 3:
                end = ' '.join(name_parts[len(name_parts) - 2:])
                name = name_parts[0] + ' ' + end
                names.add(name)
                p = {"label": "PER", "pattern": list(self.dict_entry(name))}
                patterns.append(p)

            # last 3 names
            if len(name_parts) > 3:
                last_three = name_parts[-3:]
                if any(x == last_three[0] for x in self.connectors):
                    last_three = last_three[1:]
                name = ' '.join(last_three)
                names.add(name)
                p = {"label": "PER", "pattern": list(self.dict_entry(name))}
                patterns.append(p)

            # last 2 names
            if len(name_parts) > 3:
                last_two = name_parts[-2:]
                if any(x == last_two[0] for x in self.connectors):
                    last_two = last_two[1:]
                name = ' '.join(last_two)
                names.add(name)
                p = {"label": "PER", "pattern": list(self.dict_entry(name))}
                patterns.append(p)

        for name in self.file_names:
            names.add(name)
            p = {"label": "PER", "pattern": list(self.dict_entry(name))}
            patterns.append(p)

        with open('kb_names_arranged.txt', 'wt') as f_out:
            for name in sorted(names):
                f_out.write(name + '\n')

        with open('kb_names_patterns.txt', 'wt') as f_out:
            for p in patterns:
                f_out.write(str(p['pattern']) + '\n')

        return patterns

    def build_ner(self):
        nlp = pt_core_news_sm.load(disable=["tagger", "parser"])
        self.patterns.append({'label': 'PER', 'pattern': 'Marinho e Pinto'})
        self.patterns.append({'label': 'PER', 'pattern': 'Ribeiro e Castro'})
        ruler_person_entities = EntityRuler(nlp, overwrite_ents=False)
        ruler_person_entities.add_patterns(self.patterns)
        ruler_person_entities.name = 'person_entities'
        nlp.add_pipe(ruler_person_entities, before="ner")
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

        return persons
