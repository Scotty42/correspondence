"""
Kontakte API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.database import Contact, Document
from app.models.schemas import ContactCreate, ContactUpdate, ContactResponse


router = APIRouter()


@router.get("/", response_model=list[ContactResponse])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Liste aller Kontakte"""
    result = await db.execute(
        select(Contact).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Einzelnen Kontakt abrufen"""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    return contact


@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact: ContactCreate,
    db: AsyncSession = Depends(get_db)
):
    """Neuen Kontakt anlegen"""
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    db_contact = result.scalar_one_or_none()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")

    payload = contact.model_dump(exclude_unset=True)

    # Treat explicit null as "no change"
    payload = {k: v for k, v in payload.items() if v is not None}

    # Optional: prevent explicit nulls if you don't support them
    if any(v is None for v in payload.values()):
        raise HTTPException(status_code=400, detail="Null values are not allowed")

    for key, value in payload.items():
        setattr(db_contact, key, value)

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Update violates database constraints") from e

    await db.refresh(db_contact)
    return db_contact


@router.delete("/{contact_id}")
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")

    count = await db.scalar(
        select(func.count()).select_from(Document).where(Document.contact_id == contact_id)
    ) or 0

    if count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Kontakt kann nicht gelöscht werden, da {count} Dokument(e) darauf verweisen. "
                   "Weise die Dokumente zuerst einem anderen Kontakt zu."
        )

    try:
        await db.delete(contact)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Kontakt kann nicht gelöscht werden, da Dokumente darauf verweisen.")

    return {"status": "deleted"}
