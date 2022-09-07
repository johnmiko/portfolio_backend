import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from dota.dota.main import get_interesting_games

# create_logger()
app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# http://127.0.0.1:8000/docs#/

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/dota")
async def read_item():
    print('getting interesting dota games')
    df = get_interesting_games()
    print(df.columns)
    return df.to_dict('records')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
