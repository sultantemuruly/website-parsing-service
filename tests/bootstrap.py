"""Load before other test imports (unittest does not run conftest.py)."""

import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("BRIGHTDATA_API_TOKEN", "test-token")
os.environ.setdefault("CF_ACCOUNT_ID", "test-account-id")
os.environ.setdefault("CF_API_TOKEN", "test-cf-token")
