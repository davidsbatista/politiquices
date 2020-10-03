def load_domains():
    domains = []
    with open('data/domains.txt', 'rt') as f_in:
        for line in f_in:
            if not line.startswith('#') and len(line) > 1:
                domains.append(line.strip('\n'))
    return domains
