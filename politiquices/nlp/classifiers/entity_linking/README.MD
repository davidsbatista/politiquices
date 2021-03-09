### Build an Entity Knowledge Base

    make build  
    python download_wikidata_entities.py              
    python index_wikidata_entities.py wiki_ttl/

### Concatenate all the TTL into one file to be indexed on a local SPARQL instance

    cat wiki_ttl/* | bzip2 -c > ../../webapp/fuseki-docker/fuseki-data/wikidata_org_$(date +"%Y-%m-%d").ttl.bz2