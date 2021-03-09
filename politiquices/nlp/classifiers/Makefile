.SILENT: start

classifiers:
	PYTHONPATH=$$HOME/politic-relationships/:/Users/dsbatista/politic-relationships/politiquices/classifiers/news_titles/ uvicorn --workers 2 --reload api:app

wikidata:
	$(MAKE) -C entity_linking build

all: wikidata classifiers
