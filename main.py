import asyncio

from fastapi import FastAPI, HTTPException
from crawl import crawl_page
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"status": "ok"}

@app.get("/crawl")
def crawl(url: str):
    if not url:
        return {"error": "URL is required"}
    try:
        result = asyncio.run(crawl_page(url))
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))