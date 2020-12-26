from politiquices.extraction.scripts.test_entity_linking import merge_substrings, fuzzy_match


def test_fuzzy_match_one_candidate_substring_matches_case_1():
    expanded = ['Marques Mendes']
    candidates = [{'wiki': 'Q550243', 'label': 'Luís Marques Mendes',
                  'aliases': ['Luís Manuel Gonçalves Marques Mendes']}]
    assert fuzzy_match(expanded[0], candidates[0]) is True


def test_fuzzy_match_one_candidate_substring_matches_case_2():
    expanded = ['Morais Castro']
    candidates = [{'wiki': 'Q934980', 'label': 'José Morais e Castro', 'aliases': None}]
    assert fuzzy_match(expanded[0], candidates[0]) is True


def test_fuzzy_match_one_candidate_substring_matches_case_3():
    expanded = ['Ribeiro e Castro']
    candidates = [{'wiki': 'Q1386216', 'label': 'José Ribeiro e Castro',
                   'aliases': ['José Duarte de Almeida Ribeiro e Castro']}]
    assert fuzzy_match(expanded[0], candidates[0]) is True


def test_fuzzy_match_one_candidate_substring_matches_case_4():
    expanded = ['António Marinho']
    candidates = [{'wiki': 'Q611182', 'label': 'Marinho Pinto', 'aliases': [
        'António Marinho Pinto', 'António Marinho e Pinto', 'António de Sousa Marinho e Pinto']}]
    assert fuzzy_match(expanded[0], candidates[0]) is True


def test_fuzzy_match_one_candidate_clean_string_matches_case_1():
    expanded = ['José Pedro Aguiar-Branco']
    candidates = [{'wiki': 'Q1555060', 'label': 'José Pedro Aguiar Branco',
                   'aliases': ['José Pedro Correia de Aguiar Branco']}]
    assert fuzzy_match(expanded[0], candidates[0]) is True


def test_merge_substrings():
    result = merge_substrings(['Luís Filipe Menezes', 'Dr. Menezes', 'doutor Menezes'])
    assert result == ['Luís Filipe Menezes']

    result = merge_substrings(['Pedro Silva Pereira', '”Pedro Silva Pereira'])
    assert result == ['Pedro Silva Pereira']

    result = merge_substrings(['Luís Filipe Menezes', 'Dr. Menezes', 'doutor Menezes'])
    assert result == ['Luís Filipe Menezes']

    result = merge_substrings(['Luís Marques Mendes', 'Marques Mendes'])
    assert result == ['Luís Marques Mendes']

    result = merge_substrings(['Filipe Anacoreta Correia', 'Anacoreta Correia'])
    assert result == ['Filipe Anacoreta Correia']

    result = merge_substrings(['Freitas do Amaral', 'Diogo Freitas do Amaral'])
    assert result == ['Diogo Freitas do Amaral']
