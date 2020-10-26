import csv

from datetime import datetime
from functools import reduce
from random import randint
from time import sleep


def just_sleep(upper_bound=3, verbose=False):
    sec = randint(1, upper_bound)
    if verbose:
        print(f"sleeping for {sec} seconds")
    sleep(sec)


def write_iterator_to_file(iter_struct, filename):
    with open(filename, 'wt') as f_out:
        for el in iter_struct:
            f_out.write(str(el) + '\n')


def clean_title(text):
    """
    Remove 'garbage' unimportant information from the title

    :param text:
    :return:
    """

    # ToDo: clean from match to end
    # "Catarina Martins critica escolha de ministro que defendeu Ricardo Salgado - Economia - Jornal de Neg"
    # "Catarina Martins critica escolha de ministro que defendeu Ricardo Salgado"

    text = text.strip().strip("\u200b")
    to_clean = [
        " | Rui Moreira | PÚBLICO",
        " - Weekend - Jornal de Negócios",
        " - Politica - DN",
        " - Sábado",
        " > Sociedade",
        " | DNOTICIAS.PT",
        " | Expresso.pt",
        " - Visao.pt",
        " - Notícias Lusa - SAPO Notícias",
        "Presidenciais - ",
        "Política - ",
        " - TV & Media - DN",
        " - Lusa - SAPO Notícias",
        "Visão | ",
        "Expresso | ",
        "SIC Notícias | ",
        "- Política - PUBLICO.PT",
        "- PUBLICO.PT",
        "- RTP Noticias, Áudio",
        "> Política vídeos",
        " – Observador",
        " - Observador",
        " – Obser",
        " - RTP Noticias",
        " - Renascença",
        " - Expresso.pt",
        " - JN",
        " | TVI24",
        " > TVI24",
        " > Política",
        "VIDEO - ",
        " > Geral",
        " > TV",
        " - Vídeos",
        " (C/ VIDEO)",
        " - Opinião - DN",
        "i:",
        "DNOTICIAS.PT",
        " - Lusa - SA",
        " | Económico",
        " - Sol",
        " | Diário Económico.com",
        " - PÚBLICO",
        " – O Jornal Económico",
        "DN Online: ",
        " - dn - DN",
        " - Portugal - DN",
        " - Galerias - DN",
        "- ZAP",
        "- Política",
        "- Sociedade",
        "- Economima",
        " – Página 2",
        "- Notícias",
        " - TSF",
        " - PÚBLICO",
        " - AEIOU.pt",
    ]

    return reduce(lambda a, v: a.replace(v, ""), to_clean, text)


def convert_dates(date: str):
    date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime('%Y %b')


def get_time_str():
    return datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")


def load_domains():
    domains = []
    with open('data/domains.txt', 'rt') as f_in:
        for line in f_in:
            if not line.startswith('#') and len(line) > 1:
                domains.append(line.strip('\n'))
    return domains


def read_ground_truth(filename, delimiter='\t', only_label=False):
    data = []
    with open(filename, newline="") as csvfile:
        titles = csv.reader(csvfile, delimiter=delimiter)
        for row in titles:
            if len(row) == 8:
                sample = {
                    "title": row[0],
                    "label": row[1],
                    "date": row[2],
                    "url": row[3],
                    "ent1": row[4],
                    "ent2": row[5],
                    "ent1_id": row[6],
                    "ent2_id": row[7],
                }
            else:
                sample = {
                    "title": row[0],
                    "label": row[1],
                    "date": row[2],
                    "url": row[3],
                    "ent1": row[4],
                    "ent2": row[5],
                }

            if only_label:
                if row[1]:
                    data.append(sample)
            else:
                data.append(sample)
    return data
