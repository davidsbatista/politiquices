
from politiquices.classifiers.ner.rule_based_ner import RuleBasedNer

samples = [
    {'sentence': "PSD e CDS querem ouvir Marcelo, Freitas e Castro Caldas",
     'entities': ['Marcelo', 'Freitas', 'Castro Caldas']},

    {'sentence': "Marinho e Pinto saiu do armário",
     'entities': ["Marinho e Pinto"]},

    {'sentence': "Ribeiro e Castro 'silenciado' pelo CDS",
     'entities': ["Ribeiro e Castro"]},

    {'sentence': "Fernando Cunha Guedes: financeiro “concentra” multinacional de vinhos",
     'entities': ["Fernando Cunha Guedes"]},

    {'sentence': "Passos Coelho diz que ministro da Educação cede a interesses dos sindicatos",
     'entities': ["Passos Coelho"]},

    {'sentence': "Morreu o primeiro presidente do Tribunal Constitucional, Armando Marques Guedes",
     'entities': ["Armando Marques Guedes"]},

    {'sentence': "Costa irrita-se com Pedro Santos",
     'entities': ["Costa", "Pedro Santos"]},

    {'sentence': "António Costa irrita-se com Jerónimo de Sousa",
     'entities': ["António Costa", "Jerónimo de Sousa"]},

    {'sentence': "AR - Rio gostou do debate. ″As pessoas não têm que estar a guerrear-se "
                 "com violência″",
     'entities': ["Rio"]},

    {'sentence': "Fernando Freire de Sousa sucede a Emídio Gomes na CCDR-N",
     'entities': ["Fernando Freire de Sousa", "Emídio Gomes"]},

    {'sentence': "Patologista mais influente do mundo é portuguesa. Quem é Fátima Carneiro?",
     'entities': ["Fátima Carneiro"]},

    {'sentence': "Cápsula do tempo: a primeira mulher a liderar o partido de Sá Carneiro",
     'entities': ["Sá Carneiro"]},

    {'sentence': "Vicente Moura admite excluir velejadora",
     'entities': ["Vicente Moura"]},

    {'sentence': "CGI da RTP é órgão de \"reconhecida competência e independência total\" , "
                 "diz Marques Guedes",
     'entities': ["Marques Guedes"]},

    {'sentence': "País - ASPP recebe demissão de Guedes da Silva da PSP com naturalidade",
     'entities': ["Guedes da Silva"]},

    {'sentence': "Accionistas dão seis meses a Vaz Guedes para decidir futuro da Privado "
                 "Holding - Economia - PUBLICO.",
     'entities': ["Vaz Guedes"]},

    {'sentence': "Vaz Guedes pede falência e perdão de 67 milhões",
     'entities': ["Vaz Guedes"]},

    {'sentence': "Sindicato da Carreira de Chefes da PSP defende que demissão de Guedes da Silva "
                 "só peca por tarde",
     'entities': ["Guedes da Silva"]},

    {'sentence': "Marques Guedes. Governo vê com “tranquilidade” queda de 0,7% do PIB no "
                 "1.º trimestre",
     'entities': ["Marques Guedes"]},

    {'sentence': "Durão Barroso critica Alemanha por rejeitar aumento do fundo financeiro",
     'entities': ["Durão Barroso"]},

    {'sentence': "Santana Lopes dá \"razão\" a Marcelo em pedir \"ambição por mais crescimento\"",
     'entities': ['Santana Lopes', 'Marcelo']},

    {'sentence': "Pedro Soares desafia Domingues a mostrar SMS",
     'entities': ['Pedro Soares', 'Domingues']},

    {'sentence': "Rui Pedro Soares defende José Sócrates e pede-lhe desculpas",
     'entities': ['Rui Pedro Soares', 'José Sócrates']},

    {'sentence': "Pedro Soares dos Santos: \"Costa é o único neste momento capaz de "
                 "construir consensos\"",
     'entities': ["Pedro Soares dos Santos", "Costa"]},

    {'sentence': "Maria da Graça Carvalho e a urgência em combater o fosso de género na era digital",
     'entities': ["Maria da Graça Carvalho"]}
]


def main():

    # parameters to play around:
    #   - EntityRuler(nlp, overwrite_ents=False) or EntityRuler(nlp, overwrite_ents=True)
    #   - EntityRuler: before="ner", after="ner
    #   - tag(all_entites=False|True)

    rule_ner = RuleBasedNer()
    errors = 0
    for s in samples:
        expected_entities = s['entities']
        entities, persons = rule_ner.tag(s['sentence'], all_entities=False)
        if persons != expected_entities:
            errors += 1
            print(s['sentence'])
            print()
            print("all entities:    ", entities)
            print("expected:        ", expected_entities)
            print("rule persons :   ", persons)
            print(persons == expected_entities)
            print("\n--------------")
    print("\n")
    print(rule_ner.ner.pipeline)
    ner_model = rule_ner.ner.pipeline[0][0]
    ner_rules = rule_ner.ner.pipeline[0][1]
    print("total analysed: ", len(samples))
    print("errors: ", errors)


if __name__ == '__main__':
    main()
