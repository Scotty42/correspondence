"""
Kontakte API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Contact
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
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Kontakt aktualisieren"""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    db_contact = result.scalar_one_or_none()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    
    for key, value in contact.model_dump(exclude_unset=True).items():
        setattr(db_contact, key, value)
    
    await db.commit()
    await db.refresh(db_contact)
    return db_contact


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Kontakt löschen"""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    db_contact = result.scalar_one_or_none()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    
    await db.delete(db_contact)
    await db.commit()
    return {"message": "Kontakt gelöscht"}
