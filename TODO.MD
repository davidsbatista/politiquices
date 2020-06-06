http://markneumann.xyz/blog/dependency_matcher/


## Relationship Classifier

    supports(ent1,ent2):    ent1 supports/agrees ent2 [on something]
    supports(ent2,ent1):    ent2 supports/agrees ent1 [on something]
    opposes(ent1,ent2) :    ent1 accuses/disagrenees/criticizes ent2 [of something]
    opposes(ent2,ent1) :    ent2 accuses/disagrees/criticizes ent1 [of something]
    other              :    not a relevant relationship 

### Examples:
   
   - "Rui Rio admite ser alternativa a Passos Coelho"
   - "José Braga Gonçalves promete revelações sobre centro de sondagens dirigido por Paulo Portas"

    - acusa/discorda/critica/confronta


## Create different services
    
    - spaCy: entities PER
    - relationship classifier


## add Madeira and Azores politicians
  
    SELECT DISTINCT ?subj ?subjLabel
    WHERE {
      { ?subj wdt:P39 wd:Q19953703.
        ?subj rdfs:label ?subjLabel.}  # membros do parlamento continental
      UNION
      { ?subj wdt:P39 wd:Q1101237.
        ?subj rdfs:label ?subjLabel.}   # membros do governo regional ?
      FILTER(LANG(?subjLabel) = "pt")
    } ORDER BY ?subjLabel

## Other politicians

    https://www.wikidata.org/wiki/Q13576558
    ToDo: add everyone belonging to some portuguese party

## Run Redis Graph

    docker run -p 6379:6379 -it --rm redislabs/redisgraph