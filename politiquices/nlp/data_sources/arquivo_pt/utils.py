def load_entities():
    names = []
    with open('config_data/entities_names.txt', 'rt') as f_in:
        for line in f_in:
            if not line.startswith('#') and len(line) > 1:
                names.append(line.strip('\n'))
    return names


def load_domains():
    domains = []
    with open("config_data/domains.txt", "rt") as f_in:
        for line in f_in:
            if not line.startswith("#") and len(line) > 1:
                domains.append(line.strip("\n"))
    return domains
