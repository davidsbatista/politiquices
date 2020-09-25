### API / Classifiers
   
   - Service:
     - load classes instead raw model files 
     - Classifier API arch: https://medium.com/@8B_EC/tutorial-serving-machine-learning-models-with-fastapi-in-python-c1a27319c459
     - log when queries to ElasticSearch fail
   
   - Classifiers
     -cleaning the sentence should be done int the clf class:
        cleaned_title = clean_sentence(entry['title']).strip()
     - add also 'PER' from a hand-crafted list, see: https://spacy.io/usage/rule-based-matching
     - add publico annotated data in training a title relevancy classifier 
     - better/cleaner embeddings


### Triple Store
 - Create an RDF from all the processed JSONs
 - Infrastructure:
    - Docker: automatically load TTL into dataset in Fuseki
    - set timeout query on Fuseki
 - SPARQL queries:
        - how to get SPARQL results with empty subject for repeated statements, i.e.: image + all offices ?
        - use OR in FILTER to avoid doing two queries: 
            https://stackoverflow.com/questions/30501124/or-in-a-sparql-query


### Web App
   - do layouts 
   - listar todas pessoas
   - listar todos os partidos/organizações
   - listar pessoas com informação incompleta: foto, cargos, etc.
   - sugerir para completar:
        - https://www.politicaparatodos.pt/
        - http://demo.cratica.org/deputados/            

   - clicar numa pessoa: desenvolver mais
   - Jinga tips: https://jinja.palletsprojects.com/en/2.11.x/templates/#batch


### Wikidata / Entity Linking
 - https://elasticsearch-cheatsheet.jolicode.com/
 - Filter out ppl born before 1900