from fastapi import FastAPI
from threading import Thread

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server Awake"}

def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)

def start_server():
    t = Thread(target=run)
    t.start()