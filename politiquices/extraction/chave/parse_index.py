import json


def main():
    with open('CHAVE-Publico_94_95.jsonl', 'rt') as f_in:
        docs = [json.loads(line) for line in f_in]
        for idx, d in enumerate(docs):
            if d['category'] == 'Desporto':
                continue
            parts = d['text'].split('\n')
            print(idx)
            print(d['category'])
            print(parts[0])
            print(parts[1])
            print(parts[2])
            print("\n-----")


if __name__ == '__main__':
    main()
