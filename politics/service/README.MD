
## Documentation

- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

## Starting the API endpoint

export PYTHONPATH=/Users/dsbatista/PycharmProjects/politic-relationships/
uvicorn --workers 2 --reload api:app