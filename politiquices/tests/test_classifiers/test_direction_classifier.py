'Cavaco Silva diz que acusações de Francisco Lopes “não merecem” qualquer resposta'
'Costa recusa a responder às acusações de Passos'
'Ana Gomes rejeita acusações de Luís Amado de "má-fé" e "abuso"'
'Cavaco desvaloriza ataques de Soares no debate de ontem'
'Ferreira do Amaral congratula-se com apoio de Freitas do Amaral'
'Menezes diz que ataques de Sócrates "são sinal de fim de ciclo"'
'Joana Amaral Dias confirma convite de Paulo Campos para integrar as listas do PS'
'Passos Coelho promete melhorar programa para educação criticado por Santana Castilho'


'Joana Marques Vidal condecorada por Marcelo Rebelo de Sousa'
'Passos Coelho é acusado de imaturidade política por Santos Silva'
'Passos diz não ter nenhuma resposta para acusação de apelo patético deixada por Sócrates'


def test_find_context_between_entities():
    ent1 = 'Ana Gomes'
    ent2 = 'Luís Amado'
    title = [('Ana', 'PROPN', 'PROPN'), ('Gomes', 'PROPN', 'PROPN'),
             ('rejeita', 'VERB', '<mv>|V|PR|3S|IND|@FS-STA'),
             ('acusações', 'NOUN', '<np-idf>|N|F|P|@<ACC'),
             ('de', 'ADP', 'PRP|@N<'),
             ('Luís', 'PROPN', 'PROPN'),
             ('Amado', 'PROPN', 'PROPN'),
             ('de', 'ADP', 'PRP|@N<'),
             ('"', 'PROPN', 'PROPN'),
             ('má-fé', 'PROPN', 'PROPN'),
             ('"', 'PUNCT', 'PU|@PU'),
             ('e', 'CCONJ', '<co-prparg>|KC|@CO'),
             ('"', 'PUNCT', 'PU|@PU'),
             ('abuso', 'VERB', '<mv>|V|PS|3S|IND|@FS-STA'),
             ('"', 'PUNCT', 'PU|@PU')]

    ent1_tokens = ent1.split()
    ent2_tokens = ent2.split()

    title_text = [t[0] for t in title]

    find_sub_list(ent1_tokens, title)

