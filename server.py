from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from threading import Thread
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

def start_server():
    t = Thread(target=run)
    t.start()
