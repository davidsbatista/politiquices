import jsonlines
import pt_core_news_sm

from extract_relationships import entity_linking

from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer

nlp = pt_core_news_sm.load()
nlp.disable = ["tagger", "parser"]


def main():

    # set up the NER system
    rule_ner = RuleBasedNer()

    with jsonlines.open('extraction_spacy_small/titles_processed_no_relation.jsonl', 'r') as f_in:
        titles = list(f_in)

    f_results = jsonlines.open('results.tsv', 'w')

    for t in titles:
        persons = rule_ner.tag(t['title'])
        if len(persons) < 2:
            continue
        persons_wiki = []

        for ent in persons:
            entity = entity_linking(ent)
            if entity["wiki_id"]:
                persons_wiki.append(entity)

        if len(persons_wiki) < 2:
            continue

        result = {
            "title": t['title'],
            "entities": persons,
            "wiki": persons_wiki
        }

        f_results.write(result)


if __name__ == '__main__':
    main()
