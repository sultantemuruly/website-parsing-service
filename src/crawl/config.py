import os

from config import env_int

CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
if not CF_ACCOUNT_ID:
    raise ValueError("CF_ACCOUNT_ID is not set")
if not CF_API_TOKEN:
    raise ValueError("CF_API_TOKEN is not set")

CF_BROWSER_KEEP_ALIVE_MS = env_int("CF_BROWSER_KEEP_ALIVE_MS", 600_000, minimum=1)
CF_CDP_URL = (
    f"wss://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/"
    f"browser-rendering/devtools/browser?keep_alive={CF_BROWSER_KEEP_ALIVE_MS}"
)

MAX_CRAWL_PAGES = env_int("CRAWL_MAX_PAGES", 25, minimum=1)
MAX_DISCOVERY_DEPTH = env_int("CRAWL_MAX_DEPTH", 1, minimum=1)
PAGE_TIMEOUT_MS = env_int("CRAWL_PAGE_TIMEOUT_MS", 30_000, minimum=1)
SITE_CRAWL_SEMAPHORE_COUNT = env_int("CRAWL_SITE_SEMAPHORE_COUNT", 1, minimum=1)
