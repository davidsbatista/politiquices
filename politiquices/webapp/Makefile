
sparql:
	# start the SPARQL server and load the generated triples
	docker build -t fuseki-docker fuseki-docker/
	docker run -d -p 3030:3030 -v $(shell pwd)/triples:/usr/share/data fuseki-docker --file=/usr/share/data/sample.ttl /arquivo

web:
	# create the python venv and launch the webapp
	python3 -m venv $${HOME}/politiquices_webapp_venv; . $${HOME}/politiquices_webapp_venv/bin/activate; \
	pip install --upgrade pip; \
	pip install -r webapp/requirements.txt; \
	cd $${HOME}/politiquices/politiquices/webapp/; \
	PYTHONPATH=$${HOME}/politiquices python webapp/run-webserver.py;


all: sparql	web

