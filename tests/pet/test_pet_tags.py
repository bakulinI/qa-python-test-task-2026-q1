import allure
import httpx
import pytest

from tests.pet.test_pet_crud import _create_pet


@allure.epic("Pet")
@allure.feature("Search by tags")
class TestPetTags:
    @pytest.mark.asyncio
    @allure.title("Поиск питомцев по тегам")
    async def test_find_by_tags(self, async_client: httpx.AsyncClient) -> None:
        # ВАЖНО: возможный фейл связан с тем, что swaggerapi/petstore3:1.0.27 стабильно отдаёт 500 на POST /pet
        created = await _create_pet(
            async_client,
            name="TaggedPet",
            status="available",
            tags=[{"id": 1, "name": "mytag"}],
        )
        pet_id = created["id"]

        with allure.step("Поиск по тегу mytag"):
            resp = await async_client.get("/pet/findByTags", params=[("tags", "mytag")])

        assert resp.status_code == 200
        data = resp.json()
        ids = {p["id"] for p in data if "id" in p}
        assert pet_id in ids

        await async_client.delete(f"/pet/{pet_id}")

