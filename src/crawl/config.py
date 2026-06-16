import os

from config import env_int

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
if not CF_ACCOUNT_ID:
    raise ValueError("CF_ACCOUNT_ID is not set")
if not CF_API_TOKEN:
    raise ValueError("CF_API_TOKEN is not set")

CF_BROWSER_RUN_BASE_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/browser-rendering"
)

_RAW_CRAWL_PURPOSES = os.getenv("CF_CRAWL_PURPOSES", "ai-input")
CF_CRAWL_PURPOSES = [
    purpose.strip()
    for purpose in _RAW_CRAWL_PURPOSES.split(",")
    if purpose.strip()
]
if not CF_CRAWL_PURPOSES:
    CF_CRAWL_PURPOSES = ["ai-input"]

MAX_CRAWL_PAGES = env_int("CRAWL_MAX_PAGES", 25, minimum=1)
MAX_DISCOVERY_DEPTH = env_int("CRAWL_MAX_DEPTH", 1, minimum=1)
CRAWL_JOB_POLL_INTERVAL_MS = env_int("CRAWL_JOB_POLL_INTERVAL_MS", 1_000, minimum=1)
CRAWL_JOB_TIMEOUT_MS = env_int("CRAWL_JOB_TIMEOUT_MS", 300_000, minimum=1)
