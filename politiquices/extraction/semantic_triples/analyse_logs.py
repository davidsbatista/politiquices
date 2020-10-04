import sys
from collections import defaultdict

import jsonlines

from politiquices.extraction.utils import clean_title

not_found = defaultdict(int)


def main():
    with jsonlines.open(sys.argv[1]) as reader:
        for line in reader:

            if 'desporto' in line['entry']['linkToArchive']:
                continue

            cleaned = (clean_title(line['cleaned_title']))
            if cleaned == line['relationship']['entity_1'] or cleaned == line['relationship']['entity_2']:
                continue

            if not line['relationship']['entity_1_wiki']:
                # not_found[line['relationship']['entity_1']].append(line['cleaned_title'])
                not_found[line['relationship']['entity_1']] += 1

            if not line['relationship']['entity_2_wiki']:
                # not_found[line['relationship']['entity_2']].append(line['cleaned_title'])
                not_found[line['relationship']['entity_2']] += 1

    not_found_sorted = {k: v for k, v in
                        sorted(not_found.items(), key=lambda item: item[1], reverse=True)}

    for k, v in not_found_sorted.items():
        print(k, '\t', v)


if __name__ == '__main__':
    main()
