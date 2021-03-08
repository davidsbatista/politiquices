import re
import pt_core_news_lg


class RuleBasedNer:
    """
    A NER system with a mix of rules and statistical component based on
    spaCy EntityRuler, see: https://spacy.io/usage/rule-based-matching#entityruler

    The initialization takes two lists, from which patterns are derived

    There are 3 possible configurations

        after_ner overwrite_ner
            0          -
            1         0|1

    """

    def __init__(
        self,
        token_patterns,
        phrase_patterns,
        rule_based_ner=True,
        rule_based_before_ner=True,
        overwrite_ner=True,
    ):
        self.token_patterns = token_patterns
        self.phrase_patterns = phrase_patterns
        self.rule_based_ner = rule_based_ner
        self.rule_before_ner = rule_based_before_ner
        self.overwrite_ner = overwrite_ner
        self.patterns = self.build_token_patterns()
        self.ner = self.build_ner()

    @staticmethod
    def token_pattern(name):
        for token in name.split():
            yield {"TEXT": token}

    def build_token_patterns(self):

        # add phrase patterns
        patterns = [{"label": "PER", "pattern": name} for name in self.phrase_patterns if name]

        # add token patterns
        for name in self.token_patterns:
            if name:
                name_clean = re.sub(r"\(.*\)", "", name)  # remove text inside parenthesis
                name_clean = re.sub(r"(,.*)", " ", name_clean)  # remove comma and all text after
                name_parts = name_clean.split()

                # exactly as it is
                p = {"label": "PER", "pattern": list(self.token_pattern(name))}
                patterns.append(p)

                # first and last name
                if len(name_parts) > 2:
                    name = name_parts[0] + " " + name_parts[-1]
                    p = {"label": "PER", "pattern": list(self.token_pattern(name))}
                    patterns.append(p)

        return patterns

    def build_ner(self):
        # load spaCy PT (large) model disabling all components except the 'NER'
        nlp = pt_core_news_lg.load(
            disable=[
                "tagger",
                "parser",
                "lemmatizer",
                "tok2vec",
                "morphologizer",
                "attribute_ruler",
            ]
        )

        if self.rule_based_ner:
            config = {"overwrite_ents": self.overwrite_ner}
            entity_ruler = nlp.add_pipe("entity_ruler", first=self.rule_before_ner, config=config)
            entity_ruler.initialize(lambda: [], nlp=nlp, patterns=self.patterns)

        return nlp

    def tag(self, title):
        if self.ner is None:
            raise Exception("NER not initialized")
        doc = self.ner(title)
        return [ent.text for ent in doc.ents if ent.label_ == "PER"]
