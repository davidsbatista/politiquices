## Gold-Data annotations guidelines
    ToDo

## 0. Build a Knowledge Base for the news domain using the Wikidata annotated data

   Read the annotated ground truth data and extract from each entity:
     - the instance type
     - all the occupations from 'occupation'
     - all positions from 'position_held'
     - all the political parties from 'member of political party'
     
   Then get all persons that have an occupation, a position or belong to any party from all the
   info gathered before  
   
   # ToDo:
    #  - add Madeira and Azores politicians
    #  - add anyone that was/is member of portuguese political party
    #  - add anyone that was/is member of portuguese public institutions, e.g.: CGD, Banco Portugal
    #  - Zeinal Bava

## 1. Arquivo.pt data 

   Get news articles from arquivo.pt where politicians (`/wikidata/politicians_no_parties.json`) 
   are mentioned: 
    
       get_headlines.py
       
   1. Generates `<politician_name>_wikidata_ID.tsv` files with:
       - crawl data
       - headline
       - arquivo.pt URL
       
       
## 2. Relationship Classifier

   - Relationship Classifier

      - supports(ent1,ent2):    ent1 supports/agrees ent2 [on something]
      - supports(ent2,ent1):    ent2 supports/agrees ent1 [on something]
      - opposes(ent1,ent2) :    ent1 accuses/disagrenees/criticizes ent2 [of something]
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