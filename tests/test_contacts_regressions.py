# tests/test_contacts_regressions.py
import pytest

from httpx import AsyncClient, ASGITransport
from datetime import datetime
from sqlalchemy import select

from app.models.database import Document
 
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


async def test_contacts_item_route_trailing_slash_is_404(client):
    cid = await _create_contact(client)

    # canonical route works
    ok = await client.get(f"/api/contacts/{cid}")
    assert ok.status_code == 200, ok.text

    # trailing slash must NOT work (protect against accidental frontend regression)
    bad = await client.get(f"/api/contacts/{cid}/")
    assert bad.status_code == 404, bad.text


@pytest.mark.asyncio
async def test_contact_delete_returns_409_if_referenced(client, db_session):
    cid = await _create_contact(client)

    # Create a document referencing the contact WITHOUT calling the PDF endpoint
    doc = Document(
        contact_id=cid,
        doc_type="letter",
        doc_number="TEST-0001",
        subject="Hello",
        status="draft",
        doc_date=datetime.utcnow(),
        pdf_path=None,
    )
    db_session.add(doc)
    await db_session.commit()

    r = await client.delete(f"/api/contacts/{cid}")
    assert r.status_code == 409, r.text
    txt = r.text.lower()
    assert any(k in txt for k in ("reference", "referenz", "verweis", "verweisen")), r.text


async def test_contact_update_rejects_empty_email(client):
    """
    Contract: email uses EmailStr. Empty string must be rejected with 422.
    This prevents silently storing invalid emails.
    """
    cid = await _create_contact(client)

    u = await client.put(f"/api/contacts/{cid}", json={
        "email": ""
    })
    assert u.status_code == 422, u.text
