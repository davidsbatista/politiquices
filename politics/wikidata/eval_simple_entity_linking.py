import sys

from SPARQLWrapper import SPARQLWrapper, JSON
from functools import lru_cache

from politics.utils import just_sleep, read_ground_truth, write_iterator_to_file

ent_string = []
ent_true = []
ent_pred = []
ent_string_pred = []


def query_wikidata(entity_name):
    mappings = {
        'Costa': 'António Costa',
        'Durão': 'Durão Barroso',
        'Jerónimo': 'Jerónimo de Sousa',
        'Nobre': 'Fernando Nobre',
        'Marques Mendes': 'Luís Marques Mendes',
        'Marcelo': 'Marcelo Rebelo de Sousa',
        'Rebelo de Sousa': 'Marcelo Rebelo de Sousa',
        'Menezes': 'Luís Filipe Menezes',
        'Portas': 'Paulo Portas',
        'Soares': 'Mário Soares',
        'Santos Silva': 'Augusto Santos Silva',

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
        'Ferreira de o Amaral': 'Ferreira do Amaral',
        'Freitas de o Amaral': 'Freitas do Amaral',
        'Moreira de a Silva': 'Moreira da Silva',
        'Paula Teixeira de a Cruz': 'Paula Teixeira da Cruz',
        'Vieira de a Silva': 'Vieira da Silva'
    }

    """
    http://www.wikidata.org/entity/Q59325416,Aliança,,
    http://www.wikidata.org/entity/Q884840,Bloco de Esquerda,,
    http://www.wikidata.org/entity/Q1054298,CDS - Partido Popular,,
    http://www.wikidata.org/entity/Q63645885,CHEGA,,
    http://www.wikidata.org/entity/Q46122950,Iniciativa Liberal,,
    http://www.wikidata.org/entity/Q19694667,Juntos pelo Povo,,
    http://www.wikidata.org/entity/Q16947563,LIVRE,,
    http://www.wikidata.org/entity/Q6516904,Movimento Alternativa Socialista,,
    http://www.wikidata.org/entity/Q5899673,Movimento Esperança Portugal,2008-07-23T00:00:00Z,2012-12-12T00:00:00Z
    http://www.wikidata.org/entity/Q605026,Nova Democracia,2003-06-18T00:00:00Z,2015-09-23T00:00:00Z
    http://www.wikidata.org/entity/Q20895387,"Nós, Cidadãos!",,
    http://www.wikidata.org/entity/Q5154439,Partido Comunista de Portugal (marxista-leninista),,
    http://www.wikidata.org/entity/Q2054628,Partido Comunista dos Trabalhadores Portugueses,,
    https://www.wikidata.org/wiki/Q769829,Partido Comunista Portugues,,
    http://www.wikidata.org/entity/Q10345627,Partido Democrático Republicano,,
    http://www.wikidata.org/entity/Q1819658,Partido Democrático do Atlântico,,
    http://www.wikidata.org/entity/Q6540639,Partido Liberal-Democrata,,
    http://www.wikidata.org/entity/Q2054681,Partido Nacional Renovador,,
    http://www.wikidata.org/entity/Q1332539,Partido Operário de Unidade Socialista,,
    http://www.wikidata.org/entity/Q1851550,Partido Popular Monárquico,,
    http://www.wikidata.org/entity/Q595575,Partido Social Democrata,,
    http://www.wikidata.org/entity/Q847263,Partido Socialista,,
    http://www.wikidata.org/entity/Q2054807,Partido Socialista Revolucionário,1978-01-01T00:00:00Z,1999-01-01T00:00:00Z
    http://www.wikidata.org/entity/Q3293542,Partido Trabalhista,,
    http://www.wikidata.org/entity/Q7232654,Partido Trabalhista Português,,
    http://www.wikidata.org/entity/Q20901233,Partido Unido dos Reformados e Pensionistas,,
    http://www.wikidata.org/entity/Q10345705,Partido da Solidariedade Nacional,,
    http://www.wikidata.org/entity/Q2054840,Pessoas–Animais–Natureza,,
    http://www.wikidata.org/entity/Q1352945,Política XXI,1994-01-01T00:00:00Z,1998-01-01T00:00:00Z
    http://www.wikidata.org/entity/Q2105350,Portugal pro Vida,,
    http://www.wikidata.org/entity/Q18166125,Portugal à Frente,2015-01-01T00:00:00Z,2015-11-26T00:00:00Z
    http://www.wikidata.org/entity/Q65164025,RIR,,
    """

    entity_name = mappings.get(entity_name, entity_name)
    entity_name_parts = entity_name.split()
    entity_name_regex = '.*' + '.*'.join(entity_name_parts) + '.*'
    endpoint_url = "https://query.wikidata.org/sparql"

    query = f"""
    SELECT DISTINCT ?person ?personLabel
        WHERE {{
          {{ VALUES ?relevant_parties 
                {{ wd:Q59325416 wd:Q884840 wd:Q1054298 wd:Q63645885 wd:Q46122950 wd:Q19694667 
                   wd:Q16947563 wd:Q6516904 wd:Q5899673 wd:Q605026 wd:Q20895387 wd:Q5154439 
                   wd:Q2054628 wd:Q10345627 wd:Q1819658 wd:Q6540639 wd:Q2054681 wd:Q1332539 
                   wd:Q1851550 wd:Q595575 wd:Q847263 wd:Q2054807 wd:Q3293542 wd:Q7232654 
                   wd:Q20901233 wd:Q10345705 wd:Q2054840 wd:Q1352945 wd:Q2105350 wd:Q18166125 
                   wd:Q65164025 wd:Q769829
                }}
             ?person wdt:P102 ?relevant_parties . 
             ?person rdfs:label ?personLabel }}
        UNION
          {{ VALUES ?positions {{ wd:Q19953703 wd:Q1723031 wd:Q322459 wd:Q1101237 
                                  wd:Q43185970 wd:Q82560916 wd:Q7614320}}
            ?person p:P39 ?position_held.
            ?position_held ps:P39 ?positions .
            ?person rdfs:label ?personLabel
          }}
        
        FILTER(LANG(?personLabel) = "pt")
        FILTER(regex(?personLabel, "{entity_name_regex}", "i"))

    }} ORDER BY ?personLabel
    """

    print("querying for entity: ", entity_name_regex)

    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    return sparql.query().convert()


@lru_cache(5000)
def query(entity):
    just_sleep()
    r = query_wikidata(entity)

    return r


def main():
    data = read_ground_truth()

    count = 0

    for x in data:

        if count % 5 == 0:
            print(query.cache_info())
            print(count)

        if 'wiki' in x['ent1_id']:
            entity_str = x['ent1']
            entity_id = x['ent1_id']
            ent_string.append(entity_str)
            ent_true.append(entity_id)
            r = query(entity_str)
            if len(r['results']['bindings']) == 0:
                ent_pred.append(None)
                ent_string_pred.append(None)

            elif len(r['results']['bindings']) == 1:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])

            else:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])
            count += 1

        if 'wiki' in x['ent2_id']:
            entity_str = x['ent2']
            entity_id = x['ent2_id']

            ent_string.append(entity_str)
            ent_true.append(entity_id)
            r = query(entity_str)
            if len(r['results']['bindings']) == 0:
                ent_pred.append(None)
                ent_string_pred.append(None)

            elif len(r['results']['bindings']) == 1:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])

            else:
                ent_pred.append(r['results']['bindings'][0]['person']['value'])
                ent_string_pred.append(r['results']['bindings'][0]['personLabel']['value'])
            count += 1

    correct = []
    not_found = []
    wrong = []

    for true_string, true_id, pred_string, pred_id in zip(ent_string, ent_true, ent_string_pred, ent_pred):

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

    write_iterator_to_file(correct, 'entity_linking_correct.txt')
    write_iterator_to_file(not_found, 'entity_linking_not_found.txt')
    write_iterator_to_file(wrong, 'entity_linking_wrong.txt')

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


if __name__ == '__main__':
    main()
