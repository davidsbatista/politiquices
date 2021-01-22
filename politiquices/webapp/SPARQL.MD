
##### List the total number of persons (politicians)

    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
    SELECT COUNT(?x) WHERE {
        ?x wdt:P31 wd:Q5
    }


##### List the total number of articles

    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    
    SELECT COUNT(?x) WHERE {
      ?x my_prefix:arquivo ?y .
    }


##### List the total number of news articles by year 

    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    
    SELECT ?year COUNT(?x) WHERE {
      ?x dc:date ?date .
    }
    GROUP BY (YEAR(?date) AS ?year)
    ORDER BY ?year


##### List all the politicians and the number of articles where they occur

    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    
    # ?arquivo_doc ?title
    
    SELECT ?person_name ?person (COUNT(*) as ?count){
      ?person rdfs:label ?person_name .
      ?person wdt:P31 wd:Q5 .
      {?rel my_prefix:ent1 ?person} UNION {?rel my_prefix:ent2 ?person} .
      ?rel my_prefix:arquivo ?arquivo_doc .
      ?arquivo_doc dc:title ?title .
    }
    GROUP BY ?person_name ?person
    HAVING (count(distinct *) > 1)
    ORDER BY DESC (?count)


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


##### All the occupations, educations from a personality

    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?personLabel ?occupation_label ?educatedAt_label ?position_label
    WHERE {
      
      wd:Q182367 rdfs:label ?personLabel FILTER(LANG(?personLabel) = "pt") .
      
      wd:Q182367 p:P106 ?occupationStmnt .
      ?occupationStmnt ps:P106 ?occupation .
      ?occupation rdfs:label ?occupation_label FILTER(LANG(?occupation_label) = "pt").
      
      wd:Q182367 p:P69 ?educatedAtStmnt .
      ?educatedAtStmnt ps:P69 ?educatedAt .
      ?educatedAt rdfs:label ?educatedAt_label FILTER(LANG(?educatedAt_label) = "pt").
      
      wd:Q182367 p:P39 ?positionStmnt .
      ?positionStmnt ps:P39 ?position .
      ?position rdfs:label ?position_label FILTER(LANG(?position_label) = "pt").
    
    
    }
    LIMIT 100



### All the governments based on the persons 

    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    
    SELECT DISTINCT ?cabinet ?cabinetLabel WHERE {
      ?person wdt:P31 wd:Q5;
              wdt:P27 wd:Q45;
              p:P39 ?officeStmnt.
      ?officeStmnt ps:P39 ?office.
      OPTIONAL { ?officeStmnt pq:P580 ?start. }
      OPTIONAL { ?officeStmnt pq:P582 ?end. }  
      ?officeStmnt pq:P5054 ?cabinet. 
      ?cabinet ?x ?y.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }
    } ORDER BY ?start



### All parliaments

    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX        wd: <http://www.wikidata.org/entity/>
    
    SELECT DISTINCT ?parlamentary_term ?parlamentary_termLabel ?start ?end WHERE {
      ?parlamentary_term wdt:P31 wd:Q15238777;
                         wdt:P17 wd:Q45;
                         wdt:P571 ?start;
                         wdt:P582 ?end.
    
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }
    } 
    ORDER BY DESC (?start)
    

### All members of a parliament

    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX        wd: <http://www.wikidata.org/entity/>
    
    SELECT DISTINCT ?person ?personLabel WHERE {
      ?person wdt:P31 wd:Q5;
              wdt:P27 wd:Q45;
              p:P39 ?officeStmnt.
      
      ?officeStmnt ps:P39 ?office.
      ?officeStmnt pq:P2937 wd:Q25431189. 
    
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],pt". }
    } 
    ORDER BY DESC (?start)
    

### All position grouped by count

    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		  wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
    SELECT DISTINCT ?position_label (COUNT(?person) AS ?n)
    WHERE {
      ?person wdt:P31 wd:Q5;
           rdfs:label ?personLabel FILTER(LANG(?personLabel) = "pt") .
      ?person p:P39 ?positionStmnt .
      ?positionStmnt ps:P39 ?position .
      ?position rdfs:label ?position_label FILTER(LANG(?position_label) = "pt").
    }
    GROUP BY ?position_label
    HAVING (?n>1)
    ORDER BY DESC (?n)


### All occupation grouped by count

    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		  wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
    SELECT DISTINCT ?occupation_label (COUNT(?person) AS ?n)
    WHERE {
      ?person wdt:P31 wd:Q5;
           rdfs:label ?personLabel FILTER(LANG(?personLabel) = "pt") .
      ?person p:P106 ?occupationStmnt .
      ?occupationStmnt ps:P106 ?occupation .
      ?occupation rdfs:label ?occupation_label FILTER(LANG(?occupation_label) = "pt").
    }
    GROUP BY ?occupation_label
    HAVING (?n>1)
    ORDER BY DESC (?n)


### All 'Governo Constitucional de Portugal'


    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		  wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
    
    SELECT DISTINCT ?cabinet ?cabinetLabel (COUNT(?person) as ?n)
    WHERE {
      ?person wdt:P31 wd:Q5;
              rdfs:label ?personLabel FILTER(LANG(?personLabel) = "pt") .
      ?person p:P39 ?officeStmnt .
      ?officeStmnt ps:P39 ?office .
      ?officeStmnt pq:P5054 ?cabinet.
      ?cabinet rdfs:label ?cabinetLabel FILTER(LANG(?cabinetLabel) = "pt") .
    }
    group by ?cabinet ?cabinetLabel
    ORDER BY DESC (?n)
  
  
### Top personalities that oppose someone
    
    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX my_prefix: <http://some.namespace/with/name#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>
    PREFIX		 ns2: <http://www.w3.org/2004/02/skos/core#>
    PREFIX        wd: <http://www.wikidata.org/entity/>
    PREFIX       wds: <http://www.wikidata.org/entity/statement/>
    PREFIX       wdv: <http://www.wikidata.org/value/>
    PREFIX       wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX  wikibase: <http://wikiba.se/ontology#>
    PREFIX         p: <http://www.wikidata.org/prop/>
    PREFIX        ps: <http://www.wikidata.org/prop/statement/>
    PREFIX        pq: <http://www.wikidata.org/prop/qualifier/>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX        bd: <http://www.bigdata.com/rdf#>
    
    SELECT DISTINCT ?person_a (COUNT(?url) as ?nr_articles) {
      { ?rel my_prefix:ent1 ?person_a .
        ?rel my_prefix:type 'ent1_opposes_ent2'.
      }  
      UNION 
      { ?rel my_prefix:ent2 ?person_a .
        ?rel my_prefix:type 'ent2_opposes_ent1'.
      }
      ?rel my_prefix:arquivo ?url .
    }
    GROUP BY ?person_a
    ORDER BY DESC(?nr_articles)