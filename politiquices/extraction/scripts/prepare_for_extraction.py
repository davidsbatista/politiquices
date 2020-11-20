import os
import re

import jsonlines
import mmh3

from politiquices.extraction.utils import clean_title

arquivo_data = "../../../data/crawled"

url_keywords_ignore = ['desporto', 'opiniao', 'musica', 'cinema', 'artes', 'multimedia',
                       'foto', 'vida', 'humor', 'tv']
url_other_topic = '.*(' + '|'.join(url_keywords_ignore) + ').*'

title_keywords_ignore = ['Futebol', 'Desporto', 'Concerto de Bolso', 'Celebridades',
                         'Liga dos Campeões']


already_seen = set()


def crawled_data():
    for filename in sorted(os.listdir(arquivo_data)):
        print(f"Processing {filename}")
        with jsonlines.open(arquivo_data + "/" + filename, mode="r") as reader:
            for line in reader:
                yield line


def main():
    nr_duplicates = 0
    other_topics = 0
    considered = 0
    too_short = 0
    total = 0

    to_extract = jsonlines.open('titles_to_be_processed.jsonl', mode="w")

    for entry in crawled_data():

        total += 1

        if re.match(url_other_topic, entry['linkToArchive'], flags=re.IGNORECASE):
            other_topics += 1
            continue

        if any(keyword in entry['title'] for keyword in title_keywords_ignore):
            other_topics += 1
            continue

        # ToDo: normalize some characters
        """
        - Mota Soares: Costa "empurra as pessoas para os sistemas privados" de reformas
        - Mota Soares: Costa “empurra as pessoas para os sistemas privados” de reformas
        """

        cleaned_title = clean_title(entry['title']).strip()

        if len(cleaned_title.split()) <= 4:
            too_short += 1
            continue

        title_hash = mmh3.hash(cleaned_title, signed=False)
        if title_hash in already_seen:
            nr_duplicates += 1
            continue

        considered += 1
        already_seen.add(title_hash)
        to_extract.write(entry)

    print("total       : ", total)
    print("duplicated  : ", nr_duplicates)
    print("too_short   : ", too_short)
    print("other_topics: ", other_topics)
    print("considered  : ", considered)
    to_extract.close()


if __name__ == '__main__':
    main()