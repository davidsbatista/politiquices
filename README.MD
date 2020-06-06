## 1. Arquivo.pt data 

   Get news articles from arquivo.pt where politicians (`/wikidata/politicians_no_parties.json`) 
   are mentioned: 
    
       get_headlines.py
       
   1. Generates `<politician_name>_wikidata_ID.tsv` files with:
       - crawl data
       - headline
       - arquivo.pt URL
       
       
## 2. Relationship Classifier

   Applying classifier on arquivo.pt data:

       python apply_clf_batch.py ../arquivo.pt/crawled/José_Sócrates_Q182367.tsv
       
   1. Selects only sentence with at least two 'PER', using spaCy NER model
   2. Applies the relationship classifier to each selected sentence
   3. For the one where a class exists with score > 0.5 performs entity linking with Wikidata
   4. Generates two files: `all_results.tsv` and `entities_mappings.json`
    
   2.2 Training the classifier:
    
        python train_classifier.py 
        
   1. reads training data from `data/trained_data_political_relationships - extracted_info.tsv`
   2. saves models in `webapp/app/models`
           

## 3. Generate triples graph

   1. Generating RDF/Turtle triples on classifier output:
   
          `python all_results.tsv`
        
      outputs `sample.ttl`
  
   2. start a docker container with Apache-Jena (https://hub.docker.com/r/stain/jena-fuseki)
    
        `docker run -p 3030:3030 stain/jena-fuseki`
        
      and create/load a dataset from `sample.tll`
      
         http://localhost:3030/manage.html
        
        
        
   3. Query the graph:
     
    
    PREFIX       wdt:  <http://www.wikidata.org/prop/direct/>
    PREFIX        wd:  <http://www.wikidata.org/entity/>
    PREFIX        bd:  <http://www.bigdata.com/rdf#>
    PREFIX  wikibase:  <http://wikiba.se/ontology#>
    PREFIX      rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX 		 ns1: <http://xmlns.com/foaf/0.1/>

    SELECT DISTINCT ?person ?p ?portuguese_party ?portuguese_partyLabel{
      ?person ns1:name ?p
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
    
    PREFIX ns2: <http://purl.org/dc/elements/1.1/>
    
    SELECT ?article ?title
    WHERE {
        ?article ns2:title ?title .
    }
    LIMIT 25

---

   Federated queries: 
   
   http://sulab.org/2017/07/integrating-wikidata-and-other-linked-data-sources-federated-sparql-queries/
   
   https://stackoverflow.com/questions/53012303/using-wikidata-label-service-in-federated-queries
    