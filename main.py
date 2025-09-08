from typing import Union
import oyen
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.get("/call-oyen")
async def call_oyen():
    await oyen.ask_report_to_oyen()
    return True

