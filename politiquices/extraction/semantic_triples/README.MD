## Generate triples graph

   1. Apply models to news titles
 
     - script ingests titles and outputs classified news titles
     - filter out:
          'desporto' in URL
     
     - generate some statistics about the processed titles:
        - relevant and irrelevant: how many, what percentage of the total? 
        - what are scores for the relevant and the irrelevant?
        - for the relevant how many have not enough entities?
        - for the relevant with enough entities, how many did not matched a wiki entry?
        - relevant with enough entities, all entities matched the wiki -> Triples

   2. Generating RDF/Turtle triples on classifier output:
   
          `python create_RDF.py <classified_titles.jsonl>`
        
      outputs `sample.ttl`
