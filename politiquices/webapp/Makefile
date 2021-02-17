sparql:
	# start a container running fuseki-docker, mapping:
	#	- port 3030 on the host to port 3030 on container
	#
	# 	NOTE: this takes a while, around 10min:
	#		  build: first it just builds the image copying the big ttl files
	#			run: builds TBD files and starts the fuski-service
	#
	# 		docker exec -it <container name> </jena-fuseki/fuseki-server -v --config=/fuseki/config.ttl
	#
	docker build -t fuseki-docker fuseki-docker
	docker run -dit -p 3030:3030 fuseki-docker /init.sh  # --tdb2 # --config=/fuseki/config.ttl

env:
	# create the python venv
	python3.8 -m venv $${HOME}/politiquices_webapp_venv; . $${HOME}/politiquices_webapp_venv/bin/activate; \
	pip install --upgrade pip; \
	pip install -r webapp/requirements.txt; \


web:
	cd $${HOME}/politiquices/politiquices/webapp/; \
	PYTHONPATH=$${HOME}/politiquices python webapp/run_webserver.py;


neo4j:
	. $${HOME}/politiquices_webapp_venv/bin/activate; \
	cd $${HOME}/politiquices/politiquices/webapp/neo4j_import; \
	PYTHONPATH=$${HOME}/politiquices python compute_graph_metrics.py;
	docker run -dit -p7474:7474 -p7687:7687 -v $${HOME}/politiquices/politiquices/webapp/neo4j_import/:/var/lib/neo4j/import -e NEO4J_AUTH=neo4j/s3cr3t -e NEO4J_dbms.connector.bolt.address=0.0.0.0:7687 neo4j
	sleep 40s;
	docker exec -ti $$(docker ps | grep 'neo4j' | awk '{ print $$1 }') /var/lib/neo4j/bin/cypher-shell -u neo4j -p s3cr3t -f /var/lib/neo4j/import/load_data.cql


all: sparql	env neo4j web
