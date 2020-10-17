import os
import re

import jsonlines
import mmh3

from politiquices.extraction.utils import clean_title

arquivo_data = "../../../data/crawled"

ignore = ['desporto', 'opiniao', 'musica', 'cinema', 'artes', 'multimedia', 'foto', 'vida', 'humor']
other_topic = '.*(' + '|'.join(ignore) + ').*'

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

    to_extract = jsonlines.open('titles_to_be_processed.jsonl', mode="w")

    for entry in crawled_data():
        cleaned_title = clean_title(entry['title']).strip()
        if len(cleaned_title.split()) <= 4:
            continue
        title_hash = mmh3.hash(cleaned_title, signed=False)
        if title_hash in already_seen:
            nr_duplicates += 1
            continue
        if re.match(other_topic, entry['linkToArchive'], flags=re.IGNORECASE):
            other_topics += 1
            continue
        considered += 1
        already_seen.add(title_hash)

        to_extract.write(entry)

    print(considered)
    to_extract.close()


if __name__ == '__main__':
    main()
