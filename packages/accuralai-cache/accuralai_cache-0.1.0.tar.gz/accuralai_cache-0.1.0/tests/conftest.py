import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CORE_PATH = ROOT / "packages" / "accuralai-core"
CACHE_PATH = ROOT / "packages" / "accuralai-cache"

if str(CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORE_PATH))
if str(CACHE_PATH) not in sys.path:
    sys.path.insert(0, str(CACHE_PATH))


import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
