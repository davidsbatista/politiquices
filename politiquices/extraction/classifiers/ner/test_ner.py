import pt_core_news_lg

from politiquices.extraction.classifiers.ner.rule_based_ner import RuleBasedNer

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

    {'sentence': "AR - Rio gostou do debate. ″As pessoas não têm que estar a guerrear-se com violência″",
     'entities': ["Rio"]},

    {'sentence': "Fernando Freire de Sousa sucede a Emídio Gomes na CCDR-N",
     'entities': ["Fernando Freire de Sousa", "Emídio Gomes"]},

    {'sentence': "Patologista mais influente do mundo é portuguesa. Quem é Fátima Carneiro?",
     'entities': ["Fátima Carneiro"]},

    {'sentence': "Cápsula do tempo: a primeira mulher a liderar o partido de Sá Carneiro",
     'entities': ["Sá Carneiro"]},

    {'sentence': "Vicente Moura admite excluir velejadora",
     'entities': ["Vicente Moura"]},

    {'sentence': "CGI da RTP é órgão de \"reconhecida competência e independência total\" , diz Marques Guedes",
     'entities': ["Marques Guedes"]},

    {'sentence': "País - ASPP recebe demissão de Guedes da Silva da PSP com naturalidade",
     'entities': ["Guedes da Silva"]},

    {'sentence': "Accionistas dão seis meses a Vaz Guedes para decidir futuro da Privado Holding - Economia - PUBLICO.",
     'entities': ["Vaz Guedes"]},

    {'sentence': "Vaz Guedes pede falência e perdão de 67 milhões",
     'entities': ["Vaz Guedes"]},

    {'sentence': "Sindicato da Carreira de Chefes da PSP defende que demissão de Guedes da Silva só peca por tarde",
     'entities': ["Guedes da Silva"]},

    {'sentence': "Marques Guedes. Governo vê com “tranquilidade” queda de 0,7% do PIB no 1.º trimestre",
     'entities': ["Marques Guedes"]},

    {'sentence': "Durão Barroso critica Alemanha por rejeitar aumento do fundo financeiro",
     'entities': ["Durão Barroso"]},

    {'sentence': "Santana Lopes dá \"razão\" a Marcelo em pedir \"ambição por mais crescimento\"",
     'entities': ["Santana Lopes', Marcelo"]}]


def main():
    nlp_ner = pt_core_news_lg.load(disable=["tagger", "parser"])
    rule_ner = RuleBasedNer()

    print(rule_ner.ner.pipeline)

    for s in samples:
        expected_entities = s['entities']
        entities, persons = rule_ner.tag(s['sentence'], all_entities=True)
        if persons != expected_entities:
            print(s['sentence'])
            print()
            print("all entities:    ", entities)
            print("expected:        ", expected_entities)
            print("rule persons :   ", persons)
            print(persons == expected_entities)
            print("\n--------------")


if __name__ == '__main__':
    main()
