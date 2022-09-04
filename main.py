from fastapi import FastAPI

from dota.dota.main import get_interesting_games

app = FastAPI()


# http://127.0.0.1:8000/docs#/

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/dota")
async def read_item():
    return get_interesting_games().to_json()
