import re
import sys
from collections import defaultdict
import requests
import jsonlines

from politiquices.extraction.utils import clean_title

tokens = defaultdict(int)


def get_relevancy(title):
    url = "http://127.0.0.1:8000/relevant"
    payload = {'news_title': title}
    response = requests.request("GET", url, params=payload)
    return response.json()


def get_relationships(title):
    url = "http://127.0.0.1:8000/relationship"
    payload = {'news_title': title}
    response = requests.request("GET", url, params=payload)
    return response.json()


def get_named_entities(title):
    url = "http://127.0.0.1:8000/named_entities"
    payload = {'news_title': title}
    response = requests.request("GET", url, params=payload)
    return response.json()


def main():
    count = 0

    """"
    ruler = EntityRuler(nlp)
    patterns = [
        {"label": "PER", "pattern": "Centeno"},
        {"label": "PER", "pattern": "Negrão"},
        {"label": "PER", "pattern": "Relvas"},
        {"label": "PER", "pattern": "Marcelo"},
        {"label": "PER", "pattern": "Costa"},
        {"label": "PER", "pattern": "Coelho"},
        {"label": "PER", "pattern": "Santana"},
        {"label": "PER", "pattern": "Alegre"},
        {"label": "PER", "pattern": "Sócrates"},
        {"label": "PER", "pattern": "Granadeiro"},
        {"label": "PER", "pattern": "Ferro Rodrigues"},
        {"label": "PER", "pattern": "Durão Barroso"},

        # Rita Ferro Rodrigues
    ]

    ruler.add_patterns(patterns)
    nlp.add_pipe(ruler, last=True)
    """

    with jsonlines.open(sys.argv[1]) as reader:
        for line in reader:

            count += 1
            url_ignore = ['desporto', 'opiniao', 'musica', 'cinema', 'artes', 'multimedia', 'foto',
                          'concertos-antena2', 'vida', 'humor']

            regex_expression = '.*(' + '|'.join(url_ignore) + ').*'

            if re.match(regex_expression, line['entry']['linkToArchive'], flags=re.IGNORECASE):
                continue

            desporto = ['João Pinto', 'Sá Pinto', 'Benfica', 'Sporting', 'Desporto', 'Futebol',
                        'Ronaldo', 'Ibrahimovic', 'Guardiola', 'Bruno de Carvalho', 'Ronaldinho',
                        'Messi', 'Jorge Jesus', 'Mundial2010', 'Londres2012', 'Zidane',
                        'Sérgio Conceição']

            artes = ['Paula Rego', 'David Fonseca', 'Jorge Palma', 'Manuela Azevedo',
                     'Rui Reininho', 'Olavo Bilac', 'Ana Moura', 'Carminho']

            temas = ['Concerto de Bolso:', 'Celebridades', ' - Vida', 'Tudo sobre:']

            ignore = desporto + temas + artes
            regex_expression = '.*(' + '|'.join(ignore) + ').*'
            if re.match(regex_expression, line['entry']['title'], flags=re.IGNORECASE):
                continue

            entry = line['entry']
            cleaned_title = clean_title(entry['title']).strip()
            relevancy = get_relevancy(cleaned_title)
            if relevancy['relevant'] > 0.5:
                named_entities = get_named_entities(cleaned_title)
                print(cleaned_title, '\t', named_entities)

    """
    not_found_sorted = {k: v for k, v in
                        sorted(not_found.items(), key=lambda item: item[1], reverse=True)}

    for k, v in not_found_sorted.items():
        print(k, '\t', v)
    """


if __name__ == '__main__':
    main()
