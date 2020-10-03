from functools import lru_cache
from elasticsearch import Elasticsearch
from politiquices.extraction.commons import read_ground_truth, write_iterator_to_file

ent_string = []
ent_true = []
ent_pred = []
ent_string_pred = []

es = Elasticsearch([{"host": "localhost", "port": 9200}])


@lru_cache(5000)
def query(entity):

    # ToDo: these mappings should go to the indexing process
    mappings = {
        'Costa': 'António Costa',
        'Durão': 'Durão Barroso',
        'Ferreira de o Amaral': 'Joaquim Ferreira do Amaral',
        'Jerónimo': 'Jerónimo de Sousa',
        'Nobre': 'Fernando Nobre',
        'Marques Mendes': 'Luís Marques Mendes',
        'Marcelo': 'Marcelo Rebelo de Sousa',
        'Rebelo de Sousa': 'Marcelo Rebelo de Sousa',
        'Carrilho': 'Manuela Maria Carrilho',
        'Menezes': 'Luís Filipe Menezes',
        'Moura Guedes': 'Manuela Moura Guedes',
        'Portas': 'Paulo Portas',
        'Relvas': 'Miguel Relvas',
        'Soares': 'Mário Soares',
        'Sousa Tavares': 'Miguel Sousa Tavares',
        'Santos Silva': 'Augusto Santos Silva',
        'Santana': 'Pedro Santana Lopes',

        # due to contractions
        'Adelino Amaro de a Costa': 'Adelino Amaro da Costa',
        'Amaro de a Costa': 'Amaro da Costa',
        'Carvalho de a Silva': 'Carvalho da Silva',
        'Gomes de a Silva': 'Gomes da Silva',
        'João César de as Neves': 'João César das Neves',
        'Rui Gomes de a Silva': 'Rui Gomes da Silva',
        'Martins de a Cruz': 'Martins da Cruz',
        'Manuel de os Santos': 'Manuel dos Santos',
        'Teixeira de os Santos': 'Teixeira dos Santos',
        'Freitas de o Amaral': 'Freitas do Amaral',
        'Moreira de a Silva': 'Moreira da Silva',
        'Paula Teixeira de a Cruz': 'Paula Teixeira da Cruz',
        'Vieira de a Silva': 'Vieira da Silva'
    }

    entity = mappings.get(entity, entity)

    """
    {'wiki': 'Q3040480',
     'last_modified': '2020-06-30T19:47:49Z',
     'label': 'Duarte da Costa',
     'aliases': ['Duarte da costa']}}]}}
    """

    entity_query = ' AND '.join(entity.split(' '))
    print("query")
    print(entity_query)

    res = es.search(
        index="politicians", body={"query": {"query_string": {"query": entity_query}}}
    )

    """
    query_string = {
        "query": {
            "match": {
                "label": {
                    "query": "TEXT",
                    "OPTION": "VALUE"
                }
            }
        }
    }
    """

    if res['hits']['hits']:
        return res['hits']['hits'][0]

    return None


def main():
    data = read_ground_truth()

    count = 0

    for x in data:

        """
        if count % 5 == 0:
            print(query.cache_info())
            print(count)
        """

        if "wiki" in x["ent1_id"]:
            entity_str = x["ent1"]
            entity_id = x["ent1_id"]
            ent_string.append(entity_str)
            ent_true.append(entity_id)
            res = query(entity_str)
            print(entity_str)
            print(entity_id.split("/")[-1])
            if res:
                print(res['_source']['wiki'])
                ent_pred.append(res['_source']['wiki'])
                ent_string_pred.append(res['_source']['label'])
            else:
                ent_pred.append(None)
                ent_string_pred.append(None)
            print()
            print()
            count += 1

        if "wiki" in x["ent2_id"]:
            entity_str = x["ent2"]
            entity_id = x["ent2_id"]

            ent_string.append(entity_str)
            ent_true.append(entity_id)
            res = query(entity_str)
            print(entity_str)
            print(entity_id.split("/")[-1])
            if res:
                print(res['_source']['wiki'])
                ent_pred.append(res['_source']['wiki'])
                ent_string_pred.append(res['_source']['label'])
            else:
                ent_pred.append(None)
                ent_string_pred.append(None)
            print()
            print()
            count += 1

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
            print("should never be reached")

    print("CORRECT  : ", len(correct))
    print("NOT FOUND: ", len(not_found))
    print("WRONG    : ", len(wrong))
    print()
    print("accuracy: ", float(len(correct)) / len(ent_string))

    write_iterator_to_file(correct, "entity_linking_correct.txt")
    write_iterator_to_file(not_found, "entity_linking_not_found.txt")
    write_iterator_to_file(wrong, "entity_linking_wrong.txt")

    # accuracy:  0.7530647985989493
    # accuracy:  0.7968476357267951

    # adding some rules/matching dict
    # CORRECT: 3194
    # NOT FOUND: 628
    # WRONG: 175
    # accuracy: 0.7990993244933701

    # adding members of all portuguese parties
    # CORRECT: 3123
    # NOT FOUND: 408
    # WRONG: 466
    # accuracy: 0.7813360020015011

    # adding members of some relevant portuguese parties
    # CORRECT: 3314
    # NOT FOUND: 408
    # WRONG: 275
    # accuracy: 0.8291218413810357

    # adding members of some relevant portuguese parties + Portas and Jerónimo rule
    # CORRECT: 3432
    # NOT FOUND: 408
    # WRONG: 157
    # accuracy: 0.8586439829872404

    # + correcting contractions and adding more mappings
    # CORRECT: 3514
    # NOT FOUND: 329
    # WRONG: 154
    # accuracy: 0.8791593695271454


if __name__ == "__main__":
    main()
