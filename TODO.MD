### API / Classifiers
   - Classifiers
     - add also 'PER' from a hand-crafted list, see: https://spacy.io/usage/rule-based-matching
     - add publico annotated data in training a title relevancy classifier 
     - better/cleaner embeddings
   
   - Service: 
     - Classifier API arch: 
        https://medium.com/@8B_EC/tutorial-serving-machine-learning-models-with-fastapi-in-python-c1a27319c459
     - log when queries to ElasticSearch fail
   

### Data Processing
 - script ingests titles and outputs classified news titles
 - filter out:
      'desporto' in URL
 
 - generate some statistics about the processed titles:
    - relevant and irrelevant: how many, what percentage of the total? 
    - what are scores for the relevant and the irrelevant?
    - for the relevant how many have not enough entities?
    - for the relevant with enough entities, how many did not matched a wiki entry?
    - relevant with enough entities, all entities matched the wiki -> Triples


### Triple Store
 - Infrastructure:
    - set timeout query on Fuseki
 - SPARQL queries:
        - how to get SPARQL results with empty subject for repeated statements, i.e.: image + all offices ?
        - use OR in FILTER to avoid doing two queries:
            https://stackoverflow.com/questions/30501124/or-in-a-sparql-query


### Web App
   - do layouts
   - endpoints:
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
 - ORGS:
        Partidos Politicis
        Empresas públicos: TAP, Banco de Portugal?