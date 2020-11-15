import nltk

# https://www.linguateca.pt/Floresta/doc/VISLsymbolset-manual.html
# https://www.linguateca.pt/Floresta/index_en.html

mentioned_at_end = """MENTIONED_AT_END: {%s}""" % "<PUNCT><VERB><NOUN|PROPN|ADP>*$"
mentioned_at_end_pattern = nltk.RegexpParser(mentioned_at_end)

possessive = """POSSESSIVE_CASE: {%s}""" % "<NOUN><ADP><PROPN><PROPN|ADV|ADP>*$"
possessive_pattern = nltk.RegexpParser(possessive)

passive_voice_mark = """PASSIVE_VOICE: {%s}""" % "<AUX*>?<VERB><ADP>"
passive_voice_pattern = nltk.RegexpParser(passive_voice_mark)

# super compact and easy solution adapted from:
# https://stackoverflow.com/questions/17870544/find-starting-and-ending-indices-of-sublist-in-list


def find_sub_list(entity_tokens, title_tokens):
    sll = len(entity_tokens)
    for ind in (i for i, e in enumerate(title_tokens) if e == entity_tokens[0]):
        if title_tokens[ind : ind + sll] == entity_tokens:
            return ind, ind + sll - 1


def get_context(title_pos_tags, ent1, ent2):
    ent1_tokens = ent1.split()
    ent2_tokens = ent2.split()
    title_text = [t[0] for t in title_pos_tags]
    ent1_start, ent1_end = find_sub_list(ent1_tokens, title_text)
    ent2_start, ent2_end = find_sub_list(ent2_tokens, title_text)

    return title_pos_tags[ent1_start: ent2_end + 1]


def detect_direction(pos_tags, ent1, ent2):

    # , diz/afirma <ent2>
    if (",", "PUNCT", "PU|@PU") in pos_tags:
        last_comma_idx = max(idx for idx, val in enumerate(pos_tags) if val[0] == ",")
        patterns_found = mentioned_at_end_pattern.parse(pos_tags[last_comma_idx:])
        for t in patterns_found.subtrees():
            if t.label() == "MENTIONED_AT_END":
                return "ent2_rel_ent1", patterns_found

    context = get_context(pos_tags, ent1, ent2)

    # ataque|acusações|apoio|apelo de <ent2>
    valid_nouns = ["críticas", "acusações", "ataques", "ataque", "apoio", "apelo"]
    patterns_found = possessive_pattern.parse(context)
    for t in patterns_found.subtrees():
        if t.label() == "POSSESSIVE_CASE":
            elements = list(t)
            if (
                elements[0][0] in valid_nouns
                and elements[1][0] in ["de"]
                and ent2 in " ".join(t[0] for t in elements)
            ):
                return "ent2_rel_ent1", patterns_found

    def _check_passive(el):
        if el[1] == "VERB" and "PCP" in el[2]:
            return "verb"
        elif el[1] == "ADP" and el[0] in ["pelo", "por"]:
            return "prp"

    # passive voice
    patterns_found = passive_voice_pattern.parse(context)
    for t in patterns_found.subtrees():
        if t.label() == "PASSIVE_VOICE":
            elements = list(t)
            # print(elements)
            verb_checked = False
            prp_checked = False
            for el in elements:
                result = _check_passive(el)
                if result == "verb":
                    verb_checked = True

                if result == "prp":
                    prp_checked = True

                if verb_checked and prp_checked:
                    return "ent2_rel_ent1", patterns_found

    return "ent1_rel_ent2", None
