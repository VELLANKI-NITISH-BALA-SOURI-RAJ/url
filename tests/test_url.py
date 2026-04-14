import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_shorten_url(client: AsyncClient):
    long_url = "https://www.google.com"
    response = await client.post("/shorten", json={"long_url": long_url})
    
    assert response.status_code == 200
    data = response.json()
    # Pydantic's HttpUrl might add a trailing slash
    assert data["long_url"].strip("/") == long_url.strip("/")
    assert "short_code" in data
    assert "short_url" in data
    return data["short_code"]

@pytest.mark.asyncio
async def test_redirect_to_url(client: AsyncClient):
    # First, create a short URL
    long_url = "https://www.google.com"
    create_resp = await client.post("/shorten", json={"long_url": long_url})
    short_code = create_resp.json()["short_code"]
    
    # Now try to access it
    response = await client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].strip("/") == long_url.strip("/")

@pytest.mark.asyncio
async def test_get_stats(client: AsyncClient):
    # Create and access a URL
    long_url = "https://www.example.com"
    create_resp = await client.post("/shorten", json={"long_url": long_url})
    short_code = create_resp.json()["short_code"]
    
    await client.get(f"/{short_code}")
    
    # Check stats
    response = await client.get(f"/api/v1/{short_code}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clicks"] >= 1
    assert data["short_code"] == short_code

@pytest.mark.asyncio
async def test_404_not_found(client: AsyncClient):
    response = await client.get("/nonexistentcode")
    assert response.status_code == 404
