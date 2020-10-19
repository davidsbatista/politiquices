import os
import re

from elasticsearch import Elasticsearch
from spacy.pipeline import EntityRuler

import pt_core_news_sm

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


class RuleBasedNer:
    def __init__(self):
        self.entities_file = os.path.join(APP_ROOT, "PER_entities.txt")
        self.connectors = ['do', 'da', 'de', 'dos']
        self.ner = None
        self.all_names = None
        self.build_patterns()

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
            names = {line.strip() for line in f_in if not line.startswith('#')}
        return list(names)

    def build_names(self, kb_names):
        names = set()

        for name in kb_names:
            name_clean = re.sub(r'\(.*\)', '', name)    # remove text inside parenthesis
            name_clean = re.sub(r'(,.*)', ' ',  name_clean)  # remove comma and all text after
            name_parts = name_clean.split()
            names.add(name_clean)

            # first and last name
            if len(name_parts) > 2:
                first_and_last = name_parts[0]+' '+name_parts[-1]
                names.add(first_and_last)

            # skip second name
            if len(name_parts) > 3:
                end = ' '.join(name_parts[len(name_parts) - 2:])
                skip_second = name_parts[0]+' '+end
                names.add(skip_second)

            # last 3 names
            if len(name_parts) > 3:
                last_three = name_parts[-3:]
                if any(x == last_three[0] for x in self.connectors):
                    last_three = last_three[1:]

                names.add(' '.join(last_three))

        """
        with open('kb_names_arranged.txt', 'wt') as f_out:
            for name in sorted(names):
                f_out.write(name+'\n')
        """

        return list(names)

    def build_patterns(self):
        file_names = self._get_names_file(self.entities_file)
        kb_names = self.build_names(self._get_names_kb())
        self.all_names = file_names + kb_names
        self.ner = self.build_ner(file_names + kb_names)

    @staticmethod
    def build_ner(names):
        patterns = []

        with open('all_names.txt', 'wt') as f_out:
            for name in sorted(names):
                f_out.write(name+'\n')

        for x in sorted(names, key=lambda x: len(x), reverse=True):
            patterns.append({'label': 'PER', 'pattern': x})

        nlp = pt_core_news_sm.load(disable=["tagger", "parser"])

        ruler_single_token = EntityRuler(nlp, overwrite_ents=False)
        ruler_single_token.add_patterns(patterns)
        ruler_single_token.name = 'single_token'

        ruler_two_tokens = EntityRuler(nlp)
        ruler_two_tokens.add_patterns([
            {'label': 'PER', 'pattern': 'Marinho e Pinto'},
            {'label': 'PER', 'pattern': 'Ribeiro e Castro'}
         ])
        ruler_two_tokens.name = 'two_tokens'
        nlp.add_pipe(ruler_two_tokens, before="ner")
        nlp.add_pipe(ruler_single_token, after="ner")

        return nlp

    def tag(self, title, all_entities=False):
        if self.ner is None:
            print("NER not initialized")
            return None

        doc = self.ner(title)
        entities = {ent.text: ent.label_ for ent in doc.ents}
        persons = []
        for k, v in entities.items():
            if k in self.all_names and v != "PER":
                persons.append(k)
            if v == "PER":
                persons.append(k)

        if all_entities:
            return entities, persons

        return persons
