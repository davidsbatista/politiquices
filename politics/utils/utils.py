from functools import reduce
from random import randint
from time import sleep


def just_sleep(upper_bound=3):
    sec = randint(1, upper_bound)
    print(f"sleeping for {sec} seconds")
    sleep(sec)


def write_iterator_to_file(iter_struct, filename):
    with open(filename, 'wt') as f_out:
        for el in iter_struct:
            f_out.write(str(el) + '\n')


def clean_sentence(text):
    to_clean = [
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
        "- Sociedade"
    ]

    return reduce(lambda a, v: a.replace(v, ""), to_clean, text)
