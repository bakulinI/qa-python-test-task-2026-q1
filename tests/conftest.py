import os
import time
from collections.abc import AsyncIterator

import httpx
import pytest


BASE_URL = os.getenv("PETSTORE_BASE_URL", "http://localhost:8080/api/v3")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session", autouse=True)
def wait_for_service(base_url: str) -> None:
    deadline = time.time() + 30
    last_exc: Exception | None = None

    with httpx.Client(base_url=base_url, timeout=2.0) as client:
        while time.time() < deadline:
            try:
                resp = client.get("/store/inventory")
                if resp.status_code == 200:
                    return
            except Exception as exc:
                last_exc = exc
            time.sleep(0.5)

    raise RuntimeError(f"Petstore service is not ready at {base_url!r}") from last_exc


@pytest.fixture(scope="function")
async def async_client(base_url: str) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        yield client
