from politiquices.extraction.utils.utils import clean_title_re


def test_clean_news_title():

    titles = [
        "Rui Rio acredita que Marcelo Rebelo de Sousa vai avançar para segundo mandato – Observador",
        "Expresso | Assunção Cristas: regresso de Manuel Monteiro “traria mágoas ao de cima”",
        """Rui Rio: "Se conseguir manter estratégia pode criar dificuldades a António Costa" | TVI24""",
        "Visão | Leis da transparência abrem guerra entre Carlos César e Ana Catarina Mendes",
        "Lisboa/Eleições: Telmo Correia nega ataques pessoais a António Costa - Lusa - SAPO Notícias",
        "Carvalho da Silva: «É importante que António Costa vença» > Política > TVI24",
        "PJ faz buscas no escritório de Rui Pena e José Luís Arnaut - Expresso.pt",
        "António Mexia e Eduardo Catroga mantêm rédeas da EDP | Económico",
        "Bispo de Leiria-Fátima: pedofilia não vai «abafar» visita do Papa > Sociedade > TVI24",
        "Jesus tem futuro. Na versão de Ratzinger - Sociedade - PUBLICO.PT",
        "Catarina Martins critica escolha de ministro que defendeu Ricardo Salgado - Economia - Jornal de Neg",
        "SIC Notícias | \"O Twitter tornou-se um grupo de opiniões de ódio\"",
        "SIC Notícias | Daesh anuncia morte de filho do líder Al-Baghdadi em ataque suicida",
        "SIC Notícias | Os Verdes levam situação do Novo Banco ao debate quinzenal com o primeiro-ministro",
        # """VIDEO - Jerónimo de Sousa e Catarina Martins trocam "galhardetes" em debate > TVI24"""

    ]

    expected = [
        "Rui Rio acredita que Marcelo Rebelo de Sousa vai avançar para segundo mandato",
        "Assunção Cristas: regresso de Manuel Monteiro “traria mágoas ao de cima”",
        """Rui Rio: "Se conseguir manter estratégia pode criar dificuldades a António Costa\"""",
        "Leis da transparência abrem guerra entre Carlos César e Ana Catarina Mendes",
        "Lisboa/Eleições: Telmo Correia nega ataques pessoais a António Costa",
        "Carvalho da Silva: «É importante que António Costa vença»",
        "PJ faz buscas no escritório de Rui Pena e José Luís Arnaut",
        "António Mexia e Eduardo Catroga mantêm rédeas da EDP",
        "Bispo de Leiria-Fátima: pedofilia não vai «abafar» visita do Papa",
        "Jesus tem futuro. Na versão de Ratzinger",
        "Catarina Martins critica escolha de ministro que defendeu Ricardo Salgado",
        "\"O Twitter tornou-se um grupo de opiniões de ódio\"",
        "Daesh anuncia morte de filho do líder Al-Baghdadi em ataque suicida",
        "Os Verdes levam situação do Novo Banco ao debate quinzenal com o primeiro-ministro",

    ]

    for original, expected in zip(titles, expected):
        result = clean_title_re(original)
        print("original: ", original)
        print("expected: ", expected)
        print("result  : ", result)
        print("\n")
        assert result == expected
