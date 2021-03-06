## Build Entity Knowledge Base

    make build  
    python get_wiki_entities.py              
    python index_wikidata.py wiki_jsons/

## Index on local SPARQL instance

    cat wiki_ttl/* | bzip2 -c > ../../../webapp/fuseki-docker/fuseki-data/wikidata_org_2020-12-13.ttl.bz2

