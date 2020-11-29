#!/bin/bash

/jena/bin/tdbloader2 -d -l /fuseki/wikidata /usr/share/data/wikidata_org.ttl.bz2
/jena/bin/tdbloader2 -d -l /fuseki/politiquices /usr/share/data/politiquices.ttl
/jena-fuseki/fuseki-server -v --config=/fuseki/config.ttl