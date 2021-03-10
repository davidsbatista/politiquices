from politiquices.nlp.classifiers.ner.rule_based_ner import RuleBasedNer

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

    {'sentence': "Maria da Graça Carvalho e a urgência em combater o fosso de género na era "
                 "digital",
     'entities': ["Maria da Graça Carvalho"]},

    {'sentence': "Entrevista de vida a Jorge Jardim Gonçalves. Líder histórico do BCP revela o "
                 "que nunca antes ousara",
     'entities': ["Jorge Jardim Gonçalves"]},

    {'sentence': "Cavaco Silva nomeou cunhada para assessorar antiga primeira-dama Maria Cavaco "
                 "Silva",
     'entities': ["Cavaco Silva", "Maria Cavaco Silva"]},

    {'sentence': "Edgar Correia e Carlos Luís Figueira expulsos do PCP",
     'entities': ["Edgar Correia", "Carlos Luís Figueira"]},

    {'sentence': "Ana Gomes propõe condecoração de Sérgio Vieira de Mello",
     'entities': ["Ana Gomes", "Sérgio Vieira de Mello"]}
]


def main():
    with open('names_phrase_patterns.txt', 'rt') as f_in:
        phrase_patterns = [line.strip() for line in f_in]

    with open('names_token_patterns.txt', 'rt') as f_in:
        token_patterns = [line.strip() for line in f_in]

    rule_ner = RuleBasedNer(token_patterns, phrase_patterns, overwrite_ner=True)
    errors = 0
    for s in samples:
        expected_entities = s['entities']
        persons = rule_ner.tag(s['sentence'])
        if persons != expected_entities:
            errors += 1
            print(s['sentence'])
            print()
            print("expected:  ", expected_entities)
            print("result  :  ", persons)
            print("\n--------------")
    print("total analysed: ", len(samples))
    print("errors: ", errors)


if __name__ == '__main__':
    main()