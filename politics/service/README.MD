
## Starting the API endpoint

- First make sure the Entity-Linking endpoint is running
         
        source ~/virtual_envs/python38/bin/activate
        PYTHONPATH=/Users/dsbatista/PycharmProjects/politic-relationships:/Users/dsbatista/PycharmProjects/politic-relationships/politics/classifiers/    
        cd wikidata/
        make build

 - After that just start the FastAPI app

        uvicorn --workers 2 --reload api:app


## Documentation

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc
