## Generate triples graph

   1. Generating RDF/Turtle triples on classifier output:
   
          `python create_RDF.py <classified_titles.jsonl>`
        
      outputs `sample.ttl`
  
   2. start a docker container with Apache-Jena (https://hub.docker.com/r/stain/jena-fuseki)
    
        `docker run -v fuseki-data:/fuseki --name=fuseki -p 3030:3030 stain/jena-fuseki`
        
        docker run -p 3030:3030 -v $(pwd)/fuseki-data:/usr/share/data atomgraph/fuseki --file=/usr/share/data/sample.ttl /ds

        
        # ./fuseki-server --file=../fuseki-data/sample.ttl /ds
        
        
      and create/load a dataset from `sample.tll`
      
         http://localhost:3030/manage.html
        
   3. Query the graph:

##### List all the politicians in the graph and the party they belong through Wikidata endpoint     

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>

    SELECT DISTINCT ?person ?p ?portuguese_party ?portuguese_partyLabel{
      ?person rdfs:label ?p
      SERVICE <https://query.wikidata.org/sparql> {
        ?person wdt:P27 wd:Q45.
        ?person wdt:P102 ?portuguese_party .
        ?portuguese_party rdfs:label ?portuguese_partyLabel
        SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". ?item rdfs:label ?label }
      }
      FILTER(LANG(?portuguese_partyLabel) = "pt")
    }
    LIMIT 10
    
---
##### List of articles mentioning support/defense of José Sócrates  
    
    PREFIX ns2: <http://purl.org/dc/elements/1.1/>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX ns2: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?rel_type ?score ?arquivo_doc ?title ?ent1 ?ent1_name ?ent2_name
    WHERE {
      ?rel my_prefix:type "ent1_supports_ent2" .
      ?rel my_prefix:score ?score .
      ?rel my_prefix:type ?rel_type .
      ?rel my_prefix:ent1 ?ent1 .
      ?rel my_prefix:ent2 wd:Q182367 .
      wd:Q182367 rdfs:label ?ent2_name .
      ?ent1 rdfs:label ?ent1_name .
      ?rel my_prefix:arquivo ?arquivo_doc .
      ?arquivo_doc dc:title ?title
    }
    LIMIT 25

---
##### List all the politicians in the graph belonging to the 'PS' through Wikidata endpoint     

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    
    SELECT DISTINCT ?person ?name ?personLabel {
      ?person wdt:P31 wd:Q5 .
      ?person ns2:prefLabel ?name
      SERVICE <https://query.wikidata.org/sparql> {
        ?person wdt:P102 wd:Q847263.
        ?person rdfs:label ?personLabel.
        FILTER(LANG(?personLabel) = "pt")
        SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". ?item rdfs:label ?label }
      }
    }

---
##### List everyone belonging to 'PS' that have ever opposed 'José Sócrates'

    PREFIX       ns1: <http://purl.org/dc/elements/1.1/>
    PREFIX       ns2: <http://www.w3.org/2004/02/skos/core#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX        wd: <http://www.wikidata.org/entity/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX        bd: <http://www.bigdata.com/rdf#>
    PREFIX       wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX  wikibase: <http://wikiba.se/ontology#>
    
    SELECT DISTINCT ?rel_type ?score ?arquivo_doc ?title ?ent1 ?ent1_name ?ent2_name
    WHERE {
      ?rel my_prefix:type "ent1_opposes_ent2" .
      ?rel my_prefix:score ?score .
      ?rel my_prefix:type ?rel_type .
      ?rel my_prefix:ent1 ?ent1 .
      ?rel my_prefix:ent2 wd:Q182367 .
      wd:Q182367 rdfs:label ?ent2_name .
      ?ent1 rdfs:label ?ent1_name .
      ?rel my_prefix:arquivo ?arquivo_doc .
      ?arquivo_doc dc:title ?title
      SERVICE <https://query.wikidata.org/sparql> {
        ?ent1 wdt:P102 wd:Q847263 .
        ?ent1 rdfs:label ?personLabel.
        FILTER(LANG(?personLabel) = "pt")
        SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". ?item rdfs:label ?label }
           }
       }
    LIMIT 25

##### 'José Sócrates' is ent2 in all type of relationships

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    
    SELECT DISTINCT ?rel_type ?arquivo_doc ?title ?ent1 ?ent1_name
    WHERE {
      {
        ?rel my_prefix:ent2 wd:Q182367 .
        ?rel my_prefix:type ?rel_type .
        ?rel my_prefix:ent1 ?ent1 .
        ?ent1 rdfs:label ?ent1_name . 
        ?rel my_prefix:arquivo ?arquivo_doc .
        ?arquivo_doc dc:title ?title }
    }


##### 'José Sócrates' is ent1 in all type of relationships

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    
    SELECT DISTINCT ?rel_type ?arquivo_doc ?title ?ent2 ?ent2_name
    WHERE {
      {
        ?rel my_prefix:ent1 wd:Q182367 .
        ?rel my_prefix:type ?rel_type .
        ?rel my_prefix:ent2 ?ent2 .
        ?ent2 rdfs:label ?ent2_name . 
        ?rel my_prefix:arquivo ?arquivo_doc .
        ?arquivo_doc dc:title ?title }
        FILTER (?rel_type != "other")
    }


##### All office positions hold by 'José Sócrates'

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?image_url ?officeLabel ?education ?start ?end WHERE {
      wd:Q182367 wdt:P18 ?image_url;
                 p:P39 ?officeStmnt.
      ?officeStmnt ps:P39 ?office.
      OPTIONAL { ?officeStmnt pq:P580 ?start. }
      OPTIONAL { ?officeStmnt pq:P582 ?end. }  
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }
    } ORDER BY ?start


##### All the wiki id from persons in the graph and the 'known as' and 'image_url' from Wikidata

    Note: some persons can have more than one picture 

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX       rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT DISTINCT ?personLabel ?item ?image_url {
      ?item wdt:P31 wd:Q5 # get all human entities from the local graph
      SERVICE <https://query.wikidata.org/sparql> {
        OPTIONAL { ?item wdt:P18 ?image_url. }
        ?item rdfs:label ?personLabel
        SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". ?item rdfs:label ?personLabel }
      }
    }
    
    Download JSON and copy to webapp/front-end/entities_in_database.json


   Getting statements values
   - https://stackoverflow.com/questions/54974504/sparql-question-how-to-return-property-labels-and-associated-date-qualifiers-fr
   - https://stackoverflow.com/questions/36023098/querying-wikidata-difference-between-p-and-wdt-default-prefix

   Federated queries: 
   - http://sulab.org/2017/07/integrating-wikidata-and-other-linked-data-sources-federated-sparql-queries/   
   - https://stackoverflow.com/questions/53012303/using-wikidata-label-service-in-federated-queries
