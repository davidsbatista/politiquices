## Relationship Classifier

   - Relationship Classifier

      - supports(ent1,ent2):    ent1 supports/agrees ent2 [on something]
      - supports(ent2,ent1):    ent2 supports/agrees ent1 [on something]
      - opposes(ent1,ent2) :    ent1 accuses/disagrees/criticizes ent2 [of something]
      - opposes(ent2,ent1) :    ent2 accuses/disagrees/criticizes ent1 [of something]
      - other              :    not a relevant relationship 

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
   
   
## Classifiers Endpoint
       
    Relationship classifier: 
        http://127.0.0.1:8000/relationship/?news_title=Costa tenta esvaziar revisão constitucional proposta por André Ventura
    
    Relevancy classifier
        http://127.0.0.1:8000/relevant?news_title=Sampaio critica política de saúde de Arcanjo
    
    Entity Linking
        http://127.0.0.1:8000/wikidata?entity=Costa

    Documenation:
    
        - http://127.0.0.1:8000/docs
        - http://127.0.0.1:8000/redoc
