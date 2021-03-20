import nltk
import pt_core_news_lg

from politiquices.nlp.utils.utils import find_sub_list


class DirectionClassifier:
    """
    use spaCy to extract morphological information

    https://www.linguateca.pt/Floresta/doc/VISLsymbolset-manual.html
    https://www.linguateca.pt/Floresta/index_en.html
    """

    def __init__(self):
        self.nlp = pt_core_news_lg.load(
            disable=[
                "tagger",
                "parser",
                "lemmatizer",
                "tok2vec",
                "ner",
                "attribute_ruler",
            ]
        )

    @staticmethod
    def _check_passive(el):
        if el[1] == "VERB" and "PCP" in el[2]:
            return "verb"
        elif el[1] == "ADP" and el[0] in ["pelo", "por"]:
            return "prp"

    @staticmethod
    def get_context(title_pos_tags, ent1, ent2):
        ent1_tokens = ent1.split()
        ent2_tokens = ent2.split()
        title_text = [t[0] for t in title_pos_tags]
        ent1_interval = find_sub_list(ent1_tokens, title_text)
        if ent1_interval:
            ent1_start, ent1_end = ent1_interval
            ent2_interval = find_sub_list(ent2_tokens, title_text)
            if ent2_interval:
                ent2_start, ent2_end = ent2_interval
                return title_pos_tags[ent1_start: ent2_end + 1]

        return None

    def get_pos_tags(self, sentence):
        doc = self.nlp(sentence)
        return [(t.text, t.pos_, t.tag_) for t in doc]

    def detect_direction(self, sentence, ent1, ent2):

        pos_tags = self.get_pos_tags(sentence)

        mentioned_at_end = """MENTIONED_AT_END: {%s}""" % "<PUNCT><VERB><NOUN|PROPN|ADP>*$"
        mentioned_at_end_pattern = nltk.RegexpParser(mentioned_at_end)

        possessive = """POSSESSIVE_CASE: {%s}""" % "<NOUN><ADP><PROPN><PROPN|ADV|ADP>*$"
        possessive_pattern = nltk.RegexpParser(possessive)

        passive_voice_mark = """PASSIVE_VOICE: {%s}""" % "<AUX*>?<VERB><ADP>"
        passive_voice_pattern = nltk.RegexpParser(passive_voice_mark)

        # , diz/afirma <ent2>
        if (",", "PUNCT", "PU|@PU") in pos_tags:
            last_comma_idx = max(idx for idx, val in enumerate(pos_tags) if val[0] == ",")
            patterns_found = mentioned_at_end_pattern.parse(pos_tags[last_comma_idx:])
            for t in patterns_found.subtrees():
                if t.label() == "MENTIONED_AT_END":
                    return "ent2_rel_ent1", patterns_found

        context = self.get_context(pos_tags, ent1, ent2)
        print(context)

        if not context:
            return "ent1_rel_ent2", None

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
