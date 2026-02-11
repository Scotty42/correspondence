# tests/test_contacts_regressions.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_contact(client: AsyncClient) -> int:
    r = await client.post("/api/contacts/", json={
        "contact_type": "company",
        "company_name": "TestCo",
        "street": "Main St 1",
        "zip_code": "12345",
        "city": "Testville",
        "country": "Deutschland",
    })
    assert r.status_code == 200, r.text
    return r.json()["id"]


async def test_contacts_item_route_trailing_slash_is_404(app):
    async with AsyncClient(app=app, base_url="http://test") as client:
        cid = await _create_contact(client)

        # canonical route works
        ok = await client.get(f"/api/contacts/{cid}")
        assert ok.status_code == 200, ok.text

        # trailing slash must NOT work (protect against accidental frontend regression)
        bad = await client.get(f"/api/contacts/{cid}/")
        assert bad.status_code == 404, bad.text


async def test_contact_delete_returns_409_if_referenced(app):
    """
    Regression test: previously DELETE caused 500 IntegrityError when documents referenced contact.
    Expected behavior: return 409 Conflict with a helpful detail.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        cid = await _create_contact(client)

        # Create a document referencing the contact (letter endpoint exists)
        r = await client.post("/api/documents/letter", json={
            "contact_id": cid,
            "subject": "Hello",
            "content": "Test content",
            "letter_type": "business",
        })
        assert r.status_code in (200, 201), r.text

        # Now delete should be conflict, not 500
        d = await client.delete(f"/api/contacts/{cid}")
        assert d.status_code == 409, d.text
        body = d.json()
        assert "detail" in body
        assert "verweis" in body["detail"].lower() or "reference" in body["detail"].lower()


async def test_contact_update_rejects_empty_email(app):
    """
    Contract: email uses EmailStr. Empty string must be rejected with 422.
    This prevents silently storing invalid emails.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        cid = await _create_contact(client)

        u = await client.put(f"/api/contacts/{cid}", json={
            "email": ""
        })
        assert u.status_code == 422, u.text
