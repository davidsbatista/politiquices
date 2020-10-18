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
        self.all_names = self.get_names_kb()
        self.patterns_one = self.build_entity_patterns(self.all_names)
        self.patterns_two = self._get_names_file(self.entities_file)

    @staticmethod
    def get_names_kb():
        es = Elasticsearch([{"host": "localhost", "port": 9200}])
        res = es.search(index="politicians",
                        body={"query": {"match_all": {}},
                              "size": 2000})
        all_names = sorted([r['_source']['label'] for r in res['hits']['hits']])

        return all_names

    def build_entity_patterns(self, kb_names):
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

        return list(names)

    def _get_names_file(self, fname):
        with open(fname, 'rt') as f_in:
            names = {line.strip() for line in f_in if not line.startswith('#')}
        return list(names)

    def build_ner(self, names):
        patterns = []
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

    def build_patterns(self, f_name):
        patterns_one = self.build_entity_patterns(all_names)
        patterns_two = self._get_names_file(f_name)
        nlp = build_ner(patterns_one + patterns_two)
        return nlp, patterns_one + patterns_two

    def replace_other_tags_with_per(entities, all_names):
        persons = []
        for k, v in entities.items():
            if k in all_names and v != "PER":
                persons.append(k)
            if v == "PER":
                persons.append(k)

        return persons


def main():
    # see: https://spacy.io/usage/rule-based-matching
    nlp = pt_core_news_sm.load(disable=["tagger", "parser"])
    nlp_with_rules, all_names = get_ner('PER_entities.txt')

    samples = [
        {'sentence': "PSD e CDS querem ouvir Marcelo, Freitas e Castro Caldas",
         'entities': ['Marcelo', 'Freitas', 'Castro Caldas']},

        {'sentence': "Marinho e Pinto saiu do armário",
         'entities': ["Marinho e Pinto"]},

        {'sentence': "Ribeiro e Castro 'silenciado' pelo CDS",
         'entities': ["Ribeiro e Castro"]},

        {'sentence': "Fernando Cunha Guedes: financeiro “concentra” multinacional de vinhos",
         'entities': ["Fernando Cunha Guedes"]},

        {'sentence': "Passos Coelho diz que ministro da Educação cede a interesses dos sindicatos",
         'entities': ["Passos Coelho"]},

        {'sentence': "Morreu o primeiro presidente do Tribunal Constitucional, Armando Marques Guedes",
         'entities': ["Armando Marques Guedes"]},

        {'sentence': "Costa irrita-se com Pedro Santos",
         'entities': ["Costa", "Pedro Santos"]},

        {'sentence': "António Costa irrita-se com Jerónimo de Sousa",
         'entities': ["António Costa", "Jerónimo de Sousa"]},

        {'sentence': "AR - Rio gostou do debate. ″As pessoas não têm que estar a guerrear-se com violência″",
         'entities': ["Rio"]},

        {'sentence': "Fernando Freire de Sousa sucede a Emídio Gomes na CCDR-N",
         'entities': ["Fernando Freire de Sousa", "Emídio Gomes"]},

        {'sentence': "Patologista mais influente do mundo é portuguesa. Quem é Fátima Carneiro?",
         'entities': ["Fátima Carneiro"]},

        {'sentence': "Cápsula do tempo: a primeira mulher a liderar o partido de Sá Carneiro",
         'entities': ["Sá Carneiro"]},

        {'sentence': "Vicente Moura admite excluir velejadora",
         'entities': ["Vicente Moura"]},

        {'sentence': "CGI da RTP é órgão de \"reconhecida competência e independência total\" , diz Marques Guedes",
         'entities': ["Marques Guedes"]},

        {'sentence': "País - ASPP recebe demissão de Guedes da Silva da PSP com naturalidade",
         'entities': ["Guedes da Silva"]},

        {'sentence': "Accionistas dão seis meses a Vaz Guedes para decidir futuro da Privado Holding - Economia - PUBLICO.",
         'entities': ["Vaz Guedes"]},

        {'sentence': "Vaz Guedes pede falência e perdão de 67 milhões",
         'entities': ["Vaz Guedes"]},

        {'sentence': "Sindicato da Carreira de Chefes da PSP defende que demissão de Guedes da Silva só peca por tarde",
         'entities': ["Guedes da Silva"]},

        {'sentence': "Marques Guedes. Governo vê com “tranquilidade” queda de 0,7% do PIB no 1.º trimestre",
         'entities': ["Marques Guedes"]},

        {'sentence': "Durão Barroso critica Alemanha por rejeitar aumento do fundo financeiro",
         'entities': ["Durão Barroso"]}

    ]

    for s in samples:
        doc_rules = nlp_with_rules(s['sentence'])
        expected_entities = s['entities']
        all_entities = {ent.text: ent.label_ for ent in doc_rules.ents}
        persons = replace_other_tags_with_per(all_entities, all_names)
        if persons != expected_entities:
            print(s['sentence'])
            print()
            print("rules all entities: ", all_entities)
            print("expected :          ", expected_entities)
            print("rule persons:       ", persons)
            print(persons == expected_entities)
            print("\n--------------")


if __name__ == '__main__':
    main()
