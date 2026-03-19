import allure
import httpx
import pytest


@allure.epic("Store")
class TestStoreInventory:
    @pytest.mark.asyncio
    @allure.title("Получение инвентаря магазина")
    async def test_get_inventory(self, async_client: httpx.AsyncClient) -> None:
        resp = await async_client.get("/store/inventory")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

