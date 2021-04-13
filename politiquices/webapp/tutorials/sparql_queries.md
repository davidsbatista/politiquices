### List the personalities in the graph

    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX  wd: <http://www.wikidata.org/entity/>

    SELECT ?x WHERE {
        ?x wdt:P31 wd:Q5
    }



### List articles in the graph

    PREFIX politiquices: <http://www.politiquices.pt/>
    PREFIX ns1: <http://purl.org/dc/elements/1.1/>
    
    SELECT ?date ?title ?article WHERE {
        ?x politiquices:url ?article .
        ?article ns1:title ?title;
                 ns1:date ?date.
    }
    LIMIT 1000



### The total number of articles

    PREFIX politiquices: <http://www.politiquices.pt/>
    
    SELECT (COUNT(?x) as ?n_artigos) WHERE {
        ?x politiquices:url ?y .
    }



### The total number of news articles grouped by year 

    PREFIX        dc: <http://purl.org/dc/elements/1.1/>
    
    SELECT ?year (COUNT(?x) as ?n_artigos) WHERE {
      ?x dc:date ?date .
    }
    GROUP BY (YEAR(?date) AS ?year)
    ORDER BY ?year



### List for each personality the total number of articles where he/she occurs

    PREFIX           wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX            wd: <http://www.wikidata.org/entity/>
    PREFIX  politiquices: <http://www.politiquices.pt/>
        
    SELECT ?person (COUNT(*) as ?count)
    WHERE {
      VALUES ?rel_values {'ent1_opposes_ent2' 'ent2_opposes_ent1' 
                          'ent1_supports_ent2' 'ent2_supports_ent1'}
      ?person wdt:P31 wd:Q5 ;
              {?rel politiquices:ent1 ?person} UNION {?rel politiquices:ent2 ?person} .
      ?rel politiquices:type ?rel_values .
    }
    GROUP BY ?person
    ORDER BY DESC (?count)



### The personalities in the graph, and the party they belong using the data from Wikidata     

    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?person ?personLabel {
      ?person wdt:P31 wd:Q5 .
      SERVICE <http://0.0.0.0:3030/wikidata/query> {
        ?person wdt:P102 wd:Q847263.
        ?person rdfs:label ?personLabel
        FILTER(LANG(?personLabel) = "pt")
      }
    }



### Get articles where someone supports José Sócrates  
    
    PREFIX politiquices: <http://www.politiquices.pt/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    
    SELECT DISTINCT ?url ?title ?ent1 ?ent1_name ?score 
    WHERE {
      ?rel politiquices:type "ent1_supports_ent2" .
      ?rel politiquices:score ?score .
      ?rel politiquices:type ?rel_type .
      ?rel politiquices:ent1 ?ent1 .
      ?rel politiquices:ent1_str ?ent1_name .
      ?rel politiquices:ent2 wd:Q182367 .
      ?rel politiquices:url ?url .
      ?url dc:title ?title
    }
    LIMIT 25



### List all the politicians in the graph belonging to the 'PS'     

    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT DISTINCT ?person ?personLabel {
      ?person wdt:P31 wd:Q5 .
      SERVICE <http://0.0.0.0:3030/wikidata/query> {
        ?person wdt:P102 wd:Q847263.
        ?person rdfs:label ?personLabel
        FILTER(LANG(?personLabel) = "pt")
      }
    }



### List everyone affiliated with 'Partido Socialista' that opposed 'José Sócrates'

    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX politiquices: <http://www.politiquices.pt/>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
        
    SELECT DISTINCT ?url ?title ?ent1 ?ent1_str ?ent1_name ?score WHERE {
      ?rel politiquices:type "ent1_opposes_ent2" .
      ?rel politiquices:score ?score .
      ?rel politiquices:type ?rel_type .
      ?rel politiquices:ent1 ?ent1 .
      ?rel politiquices:ent1_str ?ent1_str .
      ?rel politiquices:ent2 wd:Q182367 .
      ?rel politiquices:url ?url .
      ?url dc:title ?title
      {
        SELECT ?ent1 ?ent1_name WHERE 
        {
          ?ent1 wdt:P31 wd:Q5 .
          SERVICE <http://0.0.0.0:3030/wikidata/query> {
            ?ent1 wdt:P102 wd:Q847263.
            ?ent1 rdfs:label ?ent1_name
            FILTER(LANG(?ent1_name) = "pt")
          }
        }
      }
    }



### All public office positions hold by 'José Sócrates'

    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wd:  <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX ps: <http://www.wikidata.org/prop/statement/>
    PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
    
    SELECT DISTINCT ?office_title ?start ?end WHERE {
      wd:Q182367 p:P39 ?officeStmnt.
      ?officeStmnt ps:P39 ?office.
      ?office rdfs:label ?office_title. FILTER(LANG(?office_title)="pt")
      OPTIONAL { 
        ?officeStmnt pq:P580 ?start. 
        ?officeStmnt pq:P582 ?end. 
      }  
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


### Relações familiares no grafo

    SELECT DISTINCT ?person ?personLabel ?human_relationship ?other_person ?other_personLabel
    WHERE {
      values ?human_relationship { wdt:P22 wdt:P25 wdt:P3373 }
      ?person ?human_relationship ?other_person .
      {SELECT DISTINCT ?person
        WHERE {
          SERVICE <http://0.0.0.0:3030/politiquices/query> {
            ?person wdt:P31 wd:Q5 .
            {?rel politiquices:ent1 ?person} UNION {?rel politiquices:ent2 ?person} .
            ?rel politiquices:type ?rel_type FILTER(!REGEX(?rel_type,"other")) .
          }
        }
      }
      {SELECT DISTINCT ?other_person
        WHERE {
          SERVICE <http://0.0.0.0:3030/politiquices/query> {
            ?other_person wdt:P31 wd:Q5 .
            {?rel politiquices:ent1 ?other_person} UNION {?rel politiquices:ent2 ?other_person} .
            ?rel politiquices:type ?rel_type FILTER(!REGEX(?rel_type,"other")) .
          }
        }
      }
    }