import os
import re

import jsonlines
import mmh3

from politiquices.extraction.utils.utils import clean_title_re, clean_title_quotes

arquivo_data = "../../../data/crawled"

url_keywords_ignore = [
    "desporto",
    "dnsport",
    "opiniao",
    "musica",
    "cinema",
    "artes",
    "multimedia",
    "foto",
    "vida",
    "humor",
    "tv",
    "triatlo",
    "sporting",
]

url_other_topic = ".*(" + "|".join(url_keywords_ignore) + ").*"

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
]

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
    cleaning = 0

    to_extract = jsonlines.open("input_files_for_rdf/titles_to_be_processed.jsonl", mode="w")
    failed_to_clean = jsonlines.open("failed_to_clean.jsonl", mode="w")
    other_topics_log = jsonlines.open("failed_to_clean.jsonl", mode="w")
    too_short_log = jsonlines.open("too_short.jsonl", mode="w")

    for entry in crawled_data():

        total += 1

        if any(x in entry["linkToArchive"] for x in ignore_url):
            other_topics += 1
            other_topics_log.write({'title': entry["title"], 'link': entry["linkToArchive"]})
            continue

        if re.match(url_other_topic, entry["linkToArchive"], flags=re.IGNORECASE):
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

    print("total          : ", total)
    print("failed to clean: ", cleaning)
    print("duplicated     : ", nr_duplicates)
    print("too_short      : ", too_short)
    print("other_topics   : ", other_topics)
    print("considered     : ", considered)

    to_extract.close()
    failed_to_clean.close()
    too_short_log.close()
    other_topics_log.close()


if __name__ == "__main__":
    main()
