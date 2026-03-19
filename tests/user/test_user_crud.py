from typing import Any

import allure
import httpx
import pytest
import uuid


def _make_user_payload(username: str, user_id: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "username": username,
        "firstName": "First",
        "lastName": "Last",
        "email": f"{username}@example.com",
        "password": "password123",
        "phone": "1234567890",
        "userStatus": 1,
    }
    if user_id is not None:
        payload["id"] = user_id
    return payload


@allure.epic("User")
class TestUserCrud:
    @pytest.mark.asyncio
    @allure.title("Создание и получение пользователя по username")
    async def test_create_get_delete_user(self, async_client: httpx.AsyncClient) -> None:
        username = f"user_single_{uuid.uuid4().hex[:8]}"
        user_payload = _make_user_payload(username=username)

        with allure.step("Создать пользователя"):
            create_resp = await async_client.post("/user", json=user_payload)
        assert create_resp.status_code in (200, 201)

        with allure.step("Получить пользователя по username"):
            get_resp = await async_client.get(f"/user/{username}")
        assert get_resp.status_code == 200
        user = get_resp.json()
        assert user["username"] == username

        with allure.step("Удалить пользователя"):
            delete_resp = await async_client.delete(f"/user/{username}")
        assert delete_resp.status_code in (200, 204)

    @pytest.mark.asyncio
    @allure.title("Обновление пользователя по username (PUT /user/{username})")
    async def test_update_user_by_username(self, async_client: httpx.AsyncClient) -> None:
        username = f"user_update_{uuid.uuid4().hex[:8]}"
        user_payload = _make_user_payload(username=username)

        with allure.step("Создать пользователя"):
            create_resp = await async_client.post("/user", json=user_payload)
        assert create_resp.status_code in (200, 201)

        updated_payload = {
            **user_payload,
            "firstName": "UpdatedFirst",
            "lastName": "UpdatedLast",
        }

        with allure.step("Обновить пользователя по username"):
            update_resp = await async_client.put(f"/user/{username}", json=updated_payload)
        assert update_resp.status_code in (200, 201)

        with allure.step("Проверить, что данные обновились"):
            get_resp = await async_client.get(f"/user/{username}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["firstName"] == "UpdatedFirst"
        assert data["lastName"] == "UpdatedLast"

        await async_client.delete(f"/user/{username}")

    @pytest.mark.asyncio
    @allure.title("Создание нескольких пользователей списком")
    async def test_create_users_with_list(self, async_client: httpx.AsyncClient) -> None:
        users = [
            _make_user_payload(f"user_list_1_{uuid.uuid4().hex[:6]}"),
            _make_user_payload(f"user_list_2_{uuid.uuid4().hex[:6]}"),
        ]
        resp = await async_client.post("/user/createWithList", json=users)
        assert resp.status_code in (200, 201)

        for u in users:
            get_resp = await async_client.get(f"/user/{u['username']}")
            assert get_resp.status_code == 200
            await async_client.delete(f"/user/{u['username']}")

    @pytest.mark.asyncio
    @allure.title("Нельзя получить несуществующего пользователя")
    async def test_get_user_not_found(self, async_client: httpx.AsyncClient) -> None:
        resp = await async_client.get("/user/non_existing_user_123456")
        assert resp.status_code in (404, 400)

