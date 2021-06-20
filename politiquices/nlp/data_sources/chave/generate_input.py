import codecs
import json
import os

from bs4 import BeautifulSoup


def main():

    """
    chave_to_be_processed = open(
        '../../extraction_pipeline/processed_data/2021-02-12_CHAVE/CHAVE-Publico_94_95_to_be_processed.jsonl', 'wt')
    """

    input_base_path = "/Users/dsbatista/Downloads/CHAVEPublico"

    for root, dirs, files in os.walk(input_base_path):
        for news_file in files:
            file_path = os.path.join(root, news_file)
            with codecs.open(file_path, "r", encoding='latin_1') as input_file:

                # open SGML file and get text sections
                sgml_file = input_file.read().encode("utf8")
                soup = BeautifulSoup(sgml_file)

                # get article category
                for doc in soup.findAll("doc"):
                    children = doc.findChildren()

                    print(children)

                    if len(children) == 4:
                        continue

                    article_text = children[-1].getText()
                    category = children[3]

                    parts = article_text['text'].split('\n')
                    if len(parts[1].split()) > 30:
                        continue

                    print(parts[1])

                    # filter by category and extract triples
                    # if category.getText() in categories:
                    #     article_text = children[-1].getText()

    """    
    with open('../full_text_cache/CHAVE-Publico_94_95.jsonl', 'rt') as f_in:
        docs = [json.loads(line) for line in f_in]
        for idx, d in enumerate(docs):

            if d['category'] in ['Desporto', 'Diversos', 'Cultura']:
                continue

            parts = d['text'].split('\n')
            if len(parts[1].split()) > 30:
                continue

            chave_to_be_processed.write(
                json.dumps({"title": parts[1],
                            "linkToArchive": 'https://www.linguateca.pt/CHAVE?'+d['id'],
                            "tstamp": d['date']})+'\n'
            )
    """


if __name__ == '__main__':
    main()
