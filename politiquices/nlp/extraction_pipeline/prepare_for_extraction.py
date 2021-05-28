import os
import sys
from datetime import datetime

import mmh3
import jsonlines

from politiquices.nlp.utils.utils import clean_title_re, clean_title_quotes

title_keywords_ignore = [
    "Futebol",
    "Desporto",
    "Concerto de Bolso",
    "Celebridades",
    "Liga dos Campeões",
    "Sporting",
    "FC Porto"
]

ignore_url = [
    "/opiniao/",
    "blogues/Opinio",
    "dn.sapo.pt/galerias/videos/",
    "dn.sapo.pt/cartaz/",
    "/Vida/",
    "/musica/",
    "/opiniao/",
    "/desporto/",
    "/cinema/",
    "/artes/",
    "/multimedia/",
    "/foto/",
    "/benfica/",
    "/lifestyle/"
]

already_seen = set()


def crawled_data(crawls_dir):
    for filename in sorted(os.listdir(crawls_dir)):
        print(f"Processing {filename}")
        with jsonlines.open(crawls_dir + "/" + filename, mode="r") as reader:
            for line in reader:
                yield line


def main():
    nr_duplicates = 0
    other_topics = 0
    considered = 0
    too_short = 0
    total = 0
    cleaning = 0

    # create a directory to output all the results
    output_dir = datetime.today().strftime("%Y-%m-%d")
    os.makedirs(output_dir, exist_ok=True)

    to_extract = jsonlines.open(output_dir+"/titles_to_be_processed.jsonl", mode="w")
    failed_to_clean = jsonlines.open(output_dir+"/failed_to_clean.jsonl", mode="w")
    other_topics_log = jsonlines.open(output_dir+"/other_topics.jsonl", mode="w")
    too_short_log = jsonlines.open(output_dir+"/too_short.jsonl", mode="w")

    # read from a directory containing .jsonl files with crawled results
    crawls_dir = sys.argv[1]

    for entry in crawled_data(crawls_dir):

        total += 1

        if any(x.lower() in entry["linkToArchive"].lower() for x in ignore_url):
            other_topics += 1
            other_topics_log.write({'title': entry["title"], 'link': entry["linkToArchive"]})
            continue

        if any(keyword in entry["title"] for keyword in title_keywords_ignore):
            other_topics += 1
            other_topics_log.write({'title': entry["title"], 'link': entry["linkToArchive"]})
            continue

        try:
            cleaned_title = clean_title_quotes(clean_title_re(entry["title"]))
        except Exception as e:
            cleaning += 1
            failed_to_clean.write({'title': entry["title"], 'exception': str(e)})
            continue

        if len(cleaned_title.split()) <= 4:
            too_short += 1
            too_short_log.write({'title': entry["title"]})
            continue

        title_hash = mmh3.hash(cleaned_title, signed=False)
        if title_hash in already_seen:
            nr_duplicates += 1
            continue

        considered += 1
        already_seen.add(title_hash)
        to_extract.write(entry)

    to_extract.close()
    failed_to_clean.close()
    too_short_log.close()
    other_topics_log.close()

    print("\ntotal           : ", total)
    print("failed to clean : ", cleaning)
    print("duplicated      : ", nr_duplicates)
    print("too_short       : ", too_short)
    print("other_topics    : ", other_topics)
    print("considered      : ", considered)


if __name__ == "__main__":
    main()
