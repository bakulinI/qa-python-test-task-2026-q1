import asyncio
import uuid
from typing import Any

import allure
import httpx
import pytest


async def _create_pet(async_client: httpx.AsyncClient, name: str, status: str = "available") -> dict[str, Any]:
    last_resp: httpx.Response | None = None
    for _ in range(5):
        resp = await async_client.post(
            "/pet",
            json={
                "id": int(uuid.uuid4().int % 1_000_000_000),
                "name": name,
                "photoUrls": ["string"],
                "status": status,
            },
        )
        last_resp = resp
        if resp.status_code != 500:
            resp.raise_for_status()
            return resp.json()
        await asyncio.sleep(0.2)

    assert last_resp is not None
    last_resp.raise_for_status()
    return last_resp.json()


async def _create_user(async_client: httpx.AsyncClient, username: str) -> None:
    resp = await async_client.post(
        "/user",
        json={
            "username": username,
            "firstName": "First",
            "lastName": "Last",
            "email": f"{username}@example.com",
            "password": "password123",
            "phone": "1234567890",
            "userStatus": 1,
        },
    )
    resp.raise_for_status()


@allure.epic("E2E")
class TestE2EFlows:
    @pytest.mark.asyncio
    @allure.title("E2E: жизненный цикл питомца")
    async def test_pet_lifecycle(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        with allure.step("Создать питомца"):
            pet = await _create_pet(async_client, name="LifecyclePet", status="available")
        pet_id = pet["id"]

        with allure.step("Получить питомца по ID"):
            get_resp = await async_client.get(f"/pet/{pet_id}")
        assert get_resp.status_code == 200

        with allure.step("Обновить питомца"):
            updated_payload = pet | {"name": "LifecyclePetUpdated"}
            update_resp = await async_client.put("/pet", json=updated_payload)
        assert update_resp.status_code == 200

        with allure.step("Проверить обновление"):
            check_resp = await async_client.get(f"/pet/{pet_id}")
        assert check_resp.status_code == 200
        assert check_resp.json()["name"] == "LifecyclePetUpdated"

        with allure.step("Удалить питомца"):
            delete_resp = await async_client.delete(f"/pet/{pet_id}")
        assert delete_resp.status_code in (200, 204)

        with allure.step("Убедиться, что питомец удалён"):
            not_found_resp = await async_client.get(f"/pet/{pet_id}")
        assert not_found_resp.status_code in (404, 400, 500)

    @pytest.mark.asyncio
    @allure.title("E2E: поиск питомцев по статусу")
    async def test_search_pets_by_status(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        status = "pending"
        names = ["SearchFlowPet1", "SearchFlowPet2", "SearchFlowPet3"]

        with allure.step("Параллельно создать несколько питомцев с одинаковым статусом"):
            pets = await asyncio.gather(
                *(_create_pet(async_client, name=n, status=status) for n in names)
            )

        pet_ids = {p["id"] for p in pets}

        with allure.step("Найти питомцев по статусу"):
            resp = await async_client.get("/pet/findByStatus", params={"status": status})
        assert resp.status_code == 200
        returned = resp.json()
        returned_ids = {p["id"] for p in returned if "id" in p}
        assert pet_ids <= returned_ids

        with allure.step("Параллельно удалить созданных питомцев"):
            await asyncio.gather(*(async_client.delete(f"/pet/{pid}") for pid in pet_ids))

    @pytest.mark.asyncio
    @allure.title("E2E: пользователь, логин и заказ питомца")
    async def test_full_user_flow_with_order(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        username = f"e2e_user_{uuid.uuid4().hex[:8]}"
        with allure.step("Создать пользователя"):
            await _create_user(async_client, username=username)

        with allure.step("Залогиниться пользователем"):
            login_resp = await async_client.get(
                "/user/login",
                params={"username": username, "password": "password123"},
            )
        assert login_resp.status_code == 200

        with allure.step("Создать питомца для заказа"):
            pet = await _create_pet(async_client, name="E2EPet", status="available")

        with allure.step("Создать заказ на питомца"):
            order_resp = await async_client.post(
                "/store/order",
                json={
                    "petId": pet["id"],
                    "quantity": 1,
                    "status": "placed",
                    "complete": False,
                },
            )
        order_resp.raise_for_status()
        order = order_resp.json()
        order_id = order["id"]

        with allure.step("Получить заказ по ID"):
            get_order_resp = await async_client.get(f"/store/order/{order_id}")
        assert get_order_resp.status_code == 200

        with allure.step("Удалить заказ и пользователя"):
            delete_order_resp = await async_client.delete(f"/store/order/{order_id}")
            delete_user_resp = await async_client.delete(f"/user/{username}")
        assert delete_order_resp.status_code in (200, 204)
        assert delete_user_resp.status_code in (200, 204)

        await async_client.delete(f"/pet/{pet['id']}")

