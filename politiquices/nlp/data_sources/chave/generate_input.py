import os
import sys
import json
import codecs

from bs4 import BeautifulSoup


def main():
    input_base_path = sys.argv[1]
    output = 'CHAVE-Publico_94_95_to_be_processed.jsonl'
    ignored_categories = ['Desporto', 'Diversos', 'Cultura']
    full_text = open('CHAVE-Publico_94_95.jsonl', 'wt')
    with open(output, 'wt') as f_out:
        for root, dirs, files in os.walk(input_base_path):
            for news_file in files:
                file_path = os.path.join(root, news_file)
                with codecs.open(file_path, "r", encoding='latin_1') as input_file:

                    # open SGML file and get text sections
                    sgml_file = input_file.read().encode("utf8")
                    soup = BeautifulSoup(sgml_file, features="lxml")

                    # get article category
                    for doc in soup.findAll("doc"):
                        children = doc.findChildren()

                        if len(children) == 4:
                            continue

                        doc_id = children[1].getText()

                        date = children[2].getText()
                        category = children[3].getText()

                        # filter by category
                        if category in ignored_categories:
                            continue

                        article_text = children[-1].getText()
                        article_text_parts = article_text.split('\n')

                        if len(article_text_parts[1].split()) > 30:
                            continue

                        f_out.write(json.dumps(
                            {"title": article_text_parts[1],
                             "linkToArchive": 'https://www.linguateca.pt/CHAVE?'+doc_id,
                             "tstamp": f"{date[0:4]}-{date[4:6]}-{date[6:8]}"}
                        )+'\n')

                        full_text.write(
                            json.dumps(
                                {"id": doc_id,
                                 "date": f"{date[0:4]}-{date[4:6]}-{date[6:8]}",
                                 "category": category,
                                 "text": article_text}
                            )+'\n'
                        )


if __name__ == '__main__':
    main()
