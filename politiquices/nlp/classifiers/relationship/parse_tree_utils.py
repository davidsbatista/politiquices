
def get_head(tokens):
    """Gets the head token of a subtree"""
    if len(tokens) > 1:
        for token in tokens:
            if token.head not in tokens or token.head == token:
                top_token = token
                break
    else:
        top_token = tokens[0]

    return top_token


def get_dependents(token, deps=['flat:name']):
    """Get all dependents of 'token' which are connected with any of 'deps'"""
    dependents = [child for child in token.children if child.dep_ in deps]
    return dependents


def find_rel_words(doc):
    tokens = []
    for token in doc:
        # NOTE: just an 'AUX' might be wrong but sometimes spaCy wrongly tags a verb as aux
        if token.dep_ == 'ROOT' and token.pos_ in ['VERB', 'AUX']:
            tokens.append(token)
            tokens.extend(get_dependents(token, deps=['aux']))
            for tk in token.children:
                if tk.dep_ in ['advmod', 'xcomp'] and abs(tk.i-token.i) == 1:
                    tokens.append(tk)

    return sorted(tokens, key=lambda x: x.idx, reverse=False)


def find_subject(rel_tokens):
    tokens = []
    head_token = get_head(rel_tokens)
    if head_token:
        for token in head_token.children:
            if token.dep_ in ['nsubj', 'nsubj:pass']:
                tokens.extend(token.subtree)
        return sorted(tokens, key=lambda x: x.idx, reverse=False)
    return None


def get_arg(rel_tokens, subject, sentence):
    obj = []
    all_objs = []

    found_mark = False
    found_obj_nsubj = False

    # get the object
    for token in rel_tokens:
        for tk_child in token.children:
            # look for a core argument
            if tk_child.dep_ in ['obj', 'iobj']:
                if tk_child.pos_ in ['PROPN', 'NOUN']:
                    aux = []
                    dependents = [child for child in tk_child.children
                                  if child.dep_ in ['flat:name', 'case', 'det', 'conj', 'nmod']]
                    for tk_sub_child in dependents:
                        sub_dependents = [child for child in tk_sub_child.children
                                          if child.dep_ in ['conj', 'case', 'det', 'nmod']]
                        aux.extend(sub_dependents)
                    obj = sorted([tk_child] + dependents + aux, key=lambda x: x.idx, reverse=False)
                    all_objs.append(obj)

            # detect quotes
            elif tk_child.dep_ == 'ccomp':
                # ccomp/clausal complement, e.g.: diz/anuncia que
                # check that at least 2 childs of tk_child
                #   child -> mark -> "que" (SCONJ) AND
                #   child -> obj/nsubj -> _ (VERB)
                for tk in tk_child.children:
                    if found_mark and found_obj_nsubj:
                        break
                    if tk.dep_ == 'mark':
                        found_mark = True
                    if tk.dep_ in ['obj', 'nsubj']:
                        found_obj_nsubj = True

                # xcomp: open clausal complement, e.g: quer->xcomp->VERB->obj
                # ToDo:

    # ToDo: complement is on VER

    # get complement from the OBJECT
    complement = []
    for token in obj:
        for tk_child in token.children:
            if tk_child.dep_ in ['nmod', 'obl', 'acl', 'advcl']:
                complement.append(list(tk_child.subtree))

    # get complement from VERB
    for token in rel_tokens:
        for tk_child in token.children:
            if tk_child.dep_ in ['nmod', 'obl', 'advcl']:
                complement.append(list(tk_child.subtree))
            if tk_child.dep_ == 'xcomp' and abs(tk_child.i - token.i) > 1:
                complement.append(list(tk_child.subtree))

    """
    if len(all_objs) > 1:
        print(sentence)
        print("subject: ", subject)
        print("rel: ", rel_tokens)
        print("objects: ")
        for o in all_objs:
            print(o)
        print("complments: ", complement)
        print()
    """

    if found_mark and found_obj_nsubj:
        return obj, complement, True

    return obj, complement, False
