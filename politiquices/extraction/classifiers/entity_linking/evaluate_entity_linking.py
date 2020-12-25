import sys
from politiquices.extraction.classifiers.entity_linking.entitly_linking_clf import query_kb
from politiquices.extraction.utils.utils import read_ground_truth, write_iterator_to_file

ent_string = []
ent_true = []
ent_pred = []
ent_string_pred = []


def main():
    data = read_ground_truth(sys.argv[1])
    for x in data:
        if "wiki" in x["ent1_id"]:
            entity_str = x["ent1"]
            entity_id = x["ent1_id"]
            ent_string.append(entity_str)
            ent_true.append(entity_id)
            res = query_kb(entity_str, all_results=True)
            if len(res) == 1:
                ent_pred.append(res[0]['wiki'])
                ent_string_pred.append(res[0]['label'])
            elif len(res) > 1:
                print(entity_str)
                for e in res:
                    print(e)
                print("\n--------------")
            else:
                ent_pred.append(None)
                ent_string_pred.append(None)

        if "wiki" in x["ent2_id"]:
            entity_str = x["ent2"]
            entity_id = x["ent2_id"]
            ent_string.append(entity_str)
            ent_true.append(entity_id)
            res = query_kb(entity_str, all_results=True)
            if len(res) == 1:
                ent_pred.append(res[0]['wiki'])
                ent_string_pred.append(res[0]['label'])
            elif len(res) > 1:
                # ToDo:
                print(entity_str)
                for e in res:
                    print(e)
                print("\n--------------")
            else:
                ent_pred.append(None)
                ent_string_pred.append(None)

    correct = []
    not_found = []
    wrong = []

    for true_string, true_id, pred_string, pred_id in zip(
        ent_string, ent_true, ent_string_pred, ent_pred
    ):

        # entities that could not be found
        if pred_id is None:
            not_found.append((true_string, true_id))

        # correct
        elif true_id.split("/")[-1] == pred_id.split("/")[-1]:
            correct.append((true_string, true_id))

        # entities that are wrong
        elif true_id != pred_id:
            wrong.append((true_string, true_id, pred_string, pred_id))

        else:
            raise Exception("Case missed")

    print("CORRECT  : ", len(correct))
    print("NOT FOUND: ", len(not_found))
    print("WRONG    : ", len(wrong))
    print()
    print("accuracy: ", float(len(correct)) / len(ent_string))

    write_iterator_to_file(sorted(correct), "entity_linking_correct.txt")
    write_iterator_to_file(sorted(not_found), "entity_linking_not_found.txt")
    write_iterator_to_file(sorted(wrong), "entity_linking_wrong.txt")


if __name__ == "__main__":
    main()
