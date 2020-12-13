import traceback
import jsonlines
import pt_core_news_sm

from politiquices.extraction.classifiers.news_titles.relationship_direction_clf import detect_direction

nlp = pt_core_news_sm.load()
nlp.disable = ["tagger", "parser", "ner"]


def main():
    with jsonlines.open('extraction_spacy_small/titles_processed.jsonl', 'r') as f_in:
        titles = list(f_in)

    processed = jsonlines.open("extraction_spacy_small/titles_processed_with_direction.jsonl", mode="w")
    for title in titles:
        doc = nlp(title['title'])
        pos_tags = [(t.text, t.pos_, t.tag_) for t in doc]
        pred, pattern = detect_direction(pos_tags, title['entities'][0], title['entities'][1])
        new_scores = dict()
        for k, v in title['scores'].items():
            predicted = pred.replace('rel', k)

            if predicted in ['ent1_opposes_ent1', 'ent1_supports_ent1']:
                print(doc)
                print(pred)
                print(title['scores'])
                exit(-1)

            new_scores[predicted] = v

        result = {
            "title": title['title'],
            "entities": title['entities'],
            "ent_1": title['ent_1'],
            "ent_2": title['ent_2'],
            "scores": new_scores,
            "linkToArchive": title["linkToArchive"],
            "tstamp": title["tstamp"],
        }

        processed.write(result)


if __name__ == '__main__':
    main()
