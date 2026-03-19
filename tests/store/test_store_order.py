from typing import Any

import allure
import httpx
import pytest
import uuid


def _make_order_payload(pet_id: int, quantity: int = 1, status: str = "placed") -> dict[str, Any]:
    return {
        "petId": pet_id,
        "quantity": quantity,
        "status": status,
        "complete": False,
    }


@allure.epic("Store")
class TestStoreOrder:
    @pytest.mark.asyncio
    @allure.title("Создание, получение и удаление заказа")
    async def test_create_get_delete_order(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        pet_resp = await async_client.post(
            "/pet",
            json={
                "id": int(uuid.uuid4().int % 1_000_000_000),
                "name": "OrderPet",
                "photoUrls": ["string"],
                "status": "available",
            },
        )
        pet_resp.raise_for_status()
        pet = pet_resp.json()

        order_payload = _make_order_payload(pet_id=pet["id"], quantity=2)

        with allure.step("Создать заказ"):
            create_resp = await async_client.post("/store/order", json=order_payload)
        assert create_resp.status_code == 200
        order = create_resp.json()
        order_id = order["id"]

        with allure.step("Получить заказ по ID"):
            get_resp = await async_client.get(f"/store/order/{order_id}")
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        assert fetched["id"] == order_id
        assert fetched["petId"] == pet["id"]

        with allure.step("Удалить заказ"):
            delete_resp = await async_client.delete(f"/store/order/{order_id}")
        assert delete_resp.status_code in (200, 204)

        await async_client.delete(f"/pet/{pet['id']}")

    @pytest.mark.asyncio
    @allure.title("Нельзя получить заказ с некорректным ID")
    async def test_get_order_invalid_id(self, async_client: httpx.AsyncClient) -> None:
        resp = await async_client.get("/store/order/999999999")
        assert resp.status_code in (404, 400)

