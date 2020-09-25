
## Starting the API endpoint

- First make sure the Entity-Linking endpoint is running
         
        source ~/virtual_envs/python38/bin/activate
        export PYTHONPATH=/Users/dsbatista/PycharmProjects/politic-relationships/    
        cd wikidata/
        make build

 - After that just start the FastAPI app

        export PYTHONPATH=/Users/dsbatista/PycharmProjects/politic-relationships/
        uvicorn --workers 2 --reload api:app


## Documentation

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc
