import logging
import os
import time
from collections.abc import AsyncIterator

import httpx
import pytest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("petstore.tests")


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
                    logger.info("Petstore is ready at %s", base_url)
                    return
            except Exception as exc:
                last_exc = exc
                logger.warning("Petstore not ready yet: %s", exc)
            time.sleep(0.5)

    raise RuntimeError(f"Petstore service is not ready at {base_url!r}") from last_exc


async def _log_request(request: httpx.Request) -> None:
    logger.info("REQUEST %s %s", request.method, request.url)


async def _log_response(response: httpx.Response) -> None:
    logger.info("RESPONSE %s %s", response.status_code, response.url)


@pytest.fixture(scope="function")
async def async_client(base_url: str) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=10.0,
        event_hooks={
            "request": [_log_request],
            "response": [_log_response],
        },
    ) as client:
        yield client
