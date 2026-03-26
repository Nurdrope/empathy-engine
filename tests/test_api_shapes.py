import pytest
import httpx

from empathy_engine.api.server import app


@pytest.mark.anyio
async def test_multimodal_accepts_form_text_only():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/analyze/multimodal", data={"text": "I am fine"})
    assert response.status_code == 200
    payload = response.json()
    assert "result" in payload
    assert "text_analysis" in payload["result"]
    assert payload["result"]["text_analysis"].get("text") == "I am fine"


@pytest.mark.anyio
async def test_advanced_intensity_accepts_text_analysis():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        analysis = (await client.post("/analyze/text", json={"text": "I am okay"})).json()
        response = await client.post("/advanced/intensity", json={"analysis_result": analysis["result"]})
    assert response.status_code == 200
    payload = response.json()
    assert "result" in payload
    assert "intensity" in payload["result"]


@pytest.mark.anyio
async def test_advanced_context_accepts_text_analysis():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        analysis = (await client.post("/analyze/text", json={"text": "I am okay"})).json()
        response = await client.post("/advanced/context", json={"analysis_result": analysis["result"]})
    assert response.status_code == 200
    payload = response.json()
    assert "result" in payload
    assert "context_detected" in payload["result"]
