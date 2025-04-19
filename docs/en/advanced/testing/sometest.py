from unittest.mock import Mock


async def test_controller(client: TestClient, connection: Mock):
    response = client.get("/")
    assert response.status_code == 200
    connection.execute.assertCalled()
