# Start ElasticSearch + Kibana

    docker network create elastic
    docker run --network=elastic --name=elasticsearch -p 9200:9200 -p 9301:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.6.2
    docker run --network=elastic -p 5601:5601 docker.elastic.co/kibana/kibana:7.6.2

    Create Kibana Index pattern:
    
    http://localhost:5601/app/kibana

# Build Entity Knowledge Base

   1. Get raw data from WikiData
    
        
        mkdir wiki_jsons/
        
        python get_wiki_entities.py

   2. Index into Elastic Search
        
        
        python index_wikidata.py wiki_jsons/

   3. Evaluate annotated data against Index
   
      
        python evaluate_entity_linking.py
