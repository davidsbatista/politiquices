import json


def main():
    chave_to_be_processed = open(
        '../../extraction/processed_data/2021-02-12_CHAVE/CHAVE-Publico_94_95_to_be_processed.jsonl', 'wt')
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


if __name__ == '__main__':
    main()
