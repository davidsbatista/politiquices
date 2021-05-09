from collections import defaultdict

from politiquices.nlp.classifiers.entity_linking.entitly_linking_clf import EntityLinking
from politiquices.nlp.data_sources.articles_db import ArticlesDB
from politiquices.nlp.extraction_pipeline.extract_relationships import get_ner
from politiquices.nlp.utils.utils import read_ground_truth, write_iterator_to_file

from sklearn.metrics import accuracy_score

articles_db = ArticlesDB()
ner = get_ner()
el = EntityLinking(ner, articles_db)

ent_surface_string = []
ent_true = []
ent_pred = []
freqs = defaultdict(int)


def evaluate_one(entity_str, entity_id, url):
    res = el.entity_linking(entity_str, url)
    # 'None' as str for accuracy_sore() to work
    true = entity_id.split("/")[-1] if entity_id else 'None'
    pred = res['wiki_id'] if res else 'None'
    ent_true.append(true)
    ent_pred.append(pred)
    ent_surface_string.append(entity_str)
    freqs[entity_id] += 1


def main():
    data = read_ground_truth("../politiquices_data_v1.0.csv")
    for x in data:
        entity_one_str = x["ent1"]
        entity_one_id = x["ent1_id"]
        entity_two_str = x["ent2"]
        entity_two_id = x["ent2_id"]
        url = x['url']
        if url.startswith('http://www.publico.pt'):
            news_id = url.split("/")[-1]
            url = 'https://publico.pt/'+news_id
        evaluate_one(entity_one_str, entity_one_id, url)
        evaluate_one(entity_two_str, entity_two_id, url)

    """
    print("\n\n\n--------------------")
    for k in sorted(freqs, key=lambda x: freqs[x], reverse=True):
        print(k, '\t', freqs[k])
    """

    print("# unique ids: ", len(freqs.keys()))
    print("# named-entities (surface strings): ", len(ent_true))
    print(accuracy_score(ent_true, ent_pred))

    not_found = []
    correct = []
    wrong = []

    for ent_string, true_id, pred_id in zip(ent_surface_string, ent_true, ent_pred):
        if true_id.split("/")[-1] == pred_id.split("/")[-1]:
            correct.append((ent_string, true_id))
        elif true_id != pred_id:
            if pred_id == 'None' and true_id != 'None':
                not_found.append((ent_string, true_id))
            else:
                wrong.append((ent_string, true_id, pred_id))

    print("CORRECT  : ", len(correct))
    print("NOT FOUND: ", len(not_found))
    print("WRONG    : ", len(wrong))
    print()
    print("accuracy: ", float(len(correct)) / len(ent_true))

    write_iterator_to_file(sorted(not_found), "entity_linking_not_found.txt")
    write_iterator_to_file(sorted(wrong), "entity_linking_wrong.txt")


if __name__ == "__main__":
    main()
