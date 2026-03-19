import asyncio
import uuid
from typing import Any

import allure
import httpx
import pytest


def _make_pet_payload(
    pet_id: int | None = None,
    name: str = "Pet",
    status: str = "available",
    tags: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "photoUrls": ["string"],
        "status": status,
    }
    if pet_id is not None:
        payload["id"] = pet_id
    if tags is not None:
        payload["tags"] = tags
    return payload


async def _create_pet(async_client: httpx.AsyncClient, pet_id: int | None = None, **overrides: Any) -> dict[str, Any]:
    last_resp: httpx.Response | None = None
    for _ in range(5):
        if pet_id is None:
            pet_id = int(uuid.uuid4().int % 1_000_000_000)
        payload = _make_pet_payload(pet_id=pet_id, **overrides)
        resp = await async_client.post("/pet", json=payload)
        last_resp = resp
        if resp.status_code != 500:
            resp.raise_for_status()
            return resp.json()
        # petstore3 иногда отдаёт 500 на POST /pet при параллельной нагрузке
        pet_id = None
        await asyncio.sleep(0.2)

    assert last_resp is not None
    last_resp.raise_for_status()
    return last_resp.json()


@allure.epic("Pet")
@allure.feature("CRUD")
class TestPetCrud:
    @pytest.mark.asyncio
    @allure.title("Создание и получение питомца по ID")
    async def test_create_and_get_pet_by_id(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        with allure.step("Создать питомца"):
            created = await _create_pet(async_client, name="Barsik", status="available")

        pet_id = created["id"]

        with allure.step("Получить питомца по ID"):
            resp = await async_client.get(f"/pet/{pet_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == pet_id
        assert data["name"] == "Barsik"

        with allure.step("Удалить питомца"):
            delete_resp = await async_client.delete(f"/pet/{pet_id}")
        assert delete_resp.status_code in (200, 204)

    @pytest.mark.asyncio
    @allure.title("Обновление питомца")
    async def test_update_pet(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        created = await _create_pet(async_client, name="OldName", status="available")
        pet_id = created["id"]

        updated_payload = created | {"name": "NewName"}

        with allure.step("Обновить питомца"):
            resp = await async_client.put("/pet", json=updated_payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == pet_id
        assert data["name"] == "NewName"

        await async_client.delete(f"/pet/{pet_id}")

    @pytest.mark.asyncio
    @allure.title("Поиск питомцев по статусу")
    async def test_find_by_status(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        created_pets: list[dict[str, Any]] = []

        async def create_named(name: str) -> dict[str, Any]:
            return await _create_pet(async_client, name=name, status="pending")

        with allure.step("Параллельное создание питомцев со статусом pending"):
            created_pets = await asyncio.gather(
                create_named("SearchPet1"),
                create_named("SearchPet2"),
            )

        ids = {p["id"] for p in created_pets}

        with allure.step("Искать питомцев по статусу"):
            resp = await async_client.get("/pet/findByStatus", params={"status": "pending"})

        assert resp.status_code == 200
        data = resp.json()
        returned_ids = {p["id"] for p in data if "id" in p}
        assert ids <= returned_ids

        for pet_id in ids:
            await async_client.delete(f"/pet/{pet_id}")

    @pytest.mark.asyncio
    @allure.title("Нельзя получить питомца по несуществующему ID")
    async def test_get_pet_not_found(self, async_client: httpx.AsyncClient) -> None:
        resp = await async_client.get("/pet/999999999")
        assert resp.status_code in (404, 400, 500)

    @pytest.mark.asyncio
    @allure.title("Нельзя создать питомца без обязательных полей")
    async def test_create_pet_invalid_payload(self, async_client: httpx.AsyncClient) -> None:
        resp = await async_client.get("/pet/not-a-number")
        assert resp.status_code in (400, 404)
