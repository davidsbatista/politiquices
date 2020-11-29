sparql:
	# start a container running fuseki-docker, mapping:
	#	- port 3030 on the host to port 3030 on container
	#
	# 	NOTE: this takes a while, around 10min:
	#		  build: first it just builds the image copying the big ttl files
	#			run: builds TBD files and starts the fuski-service
	docker build -t fuseki-docker fuseki-docker
	docker run -dit -p 3030:3030 fuseki-docker /init.sh  # --tdb2 # --config=/fuseki/config.ttl


web:
	# create the python venv and launch the webapp
	python3 -m venv $${HOME}/politiquices_webapp_venv; . $${HOME}/politiquices_webapp_venv/bin/activate; \
	pip install --upgrade pip; \
	pip install -r webapp/requirements.txt; \
	cd $${HOME}/politiquices/politiquices/webapp/; \
	PYTHONPATH=$${HOME}/politiquices python webapp/run-webserver.py;


all: sparql	web