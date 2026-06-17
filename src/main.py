from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load repo-root .env before importing modules that validate env at import time.
load_dotenv(override=True)

from crawl.dependencies import get_crawl_limiter
from crawl.router import router as crawl_router
from process.router import router as process_router
from social.router import router as social_router
from summary.router import router as summary_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_crawl_limiter(app)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crawl_router)
app.include_router(process_router)
app.include_router(social_router)
app.include_router(summary_router)


@app.get("/")
async def read_root():
    return {"status": "ok"}
