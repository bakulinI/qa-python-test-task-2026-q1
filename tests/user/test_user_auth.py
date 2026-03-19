import allure
import httpx
import pytest

from tests.user.test_user_crud import _make_user_payload
import uuid


@allure.epic("User")
class TestUserAuth:
    @pytest.mark.asyncio
    @allure.title("Логин и логаут пользователя")
    async def test_login_logout(self, async_client: httpx.AsyncClient) -> None:
        username = f"user_login_{uuid.uuid4().hex[:8]}"
        user_payload = _make_user_payload(username=username)
        await async_client.post("/user", json=user_payload)

        with allure.step("Логин пользователя"):
            login_resp = await async_client.get(
                "/user/login",
                params={"username": username, "password": "password123"},
            )
        assert login_resp.status_code == 200

        with allure.step("Логаут пользователя"):
            logout_resp = await async_client.get("/user/logout")
        assert logout_resp.status_code == 200

        await async_client.delete(f"/user/{username}")

