"""
Dokumente API - Briefe, Rechnungen, Angebote
"""
from datetime import datetime, timedelta, date
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Contact, Document, NumberSequence
from app.models.schemas import (
    LetterCreate, InvoiceCreate, OfferCreate, DocumentResponse
)
from app.services.typst_renderer import TypstRenderer
from app.services.paperless_client import PaperlessClient
from app.settings import get_settings


router = APIRouter()


def to_datetime(d) -> datetime:
    """Konvertiert date zu datetime falls nötig"""
    if d is None:
        return datetime.now()
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        return datetime.combine(d, datetime.min.time())
    return datetime.now()


async def get_next_number(
    db: AsyncSession,
    prefix: str
) -> str:
    """Generiert die nächste Dokumentennummer"""
    year = datetime.now().year
    
    result = await db.execute(
        select(NumberSequence).where(
            NumberSequence.prefix == prefix,
            NumberSequence.year == year
        )
    )
    seq = result.scalar_one_or_none()
    
    if not seq:
        seq = NumberSequence(prefix=prefix, year=year, last_number=0)
        db.add(seq)
    
    seq.last_number += 1
    await db.commit()
    
    return f"{prefix}-{year}-{seq.last_number:04d}"


async def get_contact_or_404(db: AsyncSession, contact_id: int) -> Contact:
    """Lädt Kontakt oder wirft 404"""
    result = await db.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Kontakt nicht gefunden")
    return contact


def contact_to_dict(contact: Contact) -> dict:
    """Konvertiert Contact-Model zu Dict für Templates"""
    return {
        "company_name": contact.company_name,
        "salutation": contact.salutation,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "gender": contact.gender,
        "street": contact.street,
        "zip_code": contact.zip_code,
        "city": contact.city,
        "country": contact.country,
        "email": contact.email,
        "phone": contact.phone,
        "customer_number": contact.customer_number
    }


# =============================================================================
# LIST / GET
# =============================================================================

@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    doc_type: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Liste aller Dokumente"""
    query = select(Document)
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if status:
        query = query.where(Document.status == status)
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Einzelnes Dokument abrufen"""
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    return doc


@router.get("/{doc_id}/pdf")
async def get_document_pdf(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """PDF eines Dokuments herunterladen"""
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc or not doc.pdf_path:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    pdf_path = Path(doc.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF-Datei nicht gefunden")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{doc.doc_number}.pdf"
    )


# =============================================================================
# BRIEF
# =============================================================================

@router.post("/letter", response_model=DocumentResponse)
async def create_letter(
    letter: LetterCreate,
    db: AsyncSession = Depends(get_db)
):
    """Brief erstellen (Geschäfts- oder Privatbrief)"""
    settings = get_settings()
    contact = await get_contact_or_404(db, letter.contact_id)
    
    # Prefix je nach Brieftyp
    prefix = "BRF" if letter.letter_type == "business" else "PRV"
    doc_number = await get_next_number(db, prefix)
    doc_date = to_datetime(letter.doc_date)
    
    # Absenderdaten je nach Brieftyp
    sender_data = settings.get_sender(letter.letter_type)
    
    renderer = TypstRenderer()
    
    try:
        pdf_path = renderer.render_letter(
            sender=sender_data,
            contact=contact_to_dict(contact),
            subject=letter.subject,
            content=letter.content,
            doc_number=doc_number,
            doc_date=doc_date,
            letter_type=letter.letter_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF-Fehler: {str(e)}")
    
    # Dokumenttyp speichern (letter_business oder letter_private)
    doc_type = f"letter_{letter.letter_type}"
    
    doc = Document(
        doc_type=doc_type,
        doc_number=doc_number,
        contact_id=contact.id,
        subject=letter.subject,
        content=letter.content,
        doc_date=doc_date,
        status="final",
        pdf_path=str(pdf_path)
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    return doc


# =============================================================================
# RECHNUNG
# =============================================================================

@router.post("/invoice", response_model=DocumentResponse)
async def create_invoice(
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Rechnung erstellen"""
    settings = get_settings()
    contact = await get_contact_or_404(db, invoice.contact_id)
    
    doc_number = await get_next_number(db, "RG")
    doc_date = to_datetime(invoice.doc_date)
    due_date = doc_date + timedelta(days=invoice.due_days)
    
    # Positionen als Dict-Liste
    positions = [p.model_dump() for p in invoice.positions]
    
    # Kleinunternehmer-Flag aus Config
    kleinunternehmer = settings.sender.kleinunternehmer
    
    # Beträge berechnen
    net_total = sum(p["quantity"] * p["unit_price"] for p in positions)
    if kleinunternehmer:
        vat_total = 0
        gross_total = net_total
    else:
        vat_total = sum(
            p["quantity"] * p["unit_price"] * (p.get("vat_rate", 19) / 100) 
            for p in positions
        )
        gross_total = net_total + vat_total
    
    # Rechnungen immer mit geschäftlichen Absenderdaten
    sender_data = settings.get_sender("business")
    
    renderer = TypstRenderer()
    
    try:
        pdf_path = renderer.render_invoice(
            sender=sender_data,
            contact=contact_to_dict(contact),
            positions=positions,
            doc_number=doc_number,
            doc_date=doc_date,
            due_date=due_date,
            notes=invoice.notes or "",
            kleinunternehmer=kleinunternehmer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF-Fehler: {str(e)}")
    
    doc = Document(
        doc_type="invoice",
        doc_number=doc_number,
        contact_id=contact.id,
        subject=f"Rechnung {doc_number}",
        positions=positions,
        net_total=net_total,
        vat_total=vat_total,
        gross_total=gross_total,
        doc_date=doc_date,
        due_date=due_date,
        status="final",
        pdf_path=str(pdf_path)
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    return doc


# =============================================================================
# ANGEBOT
# =============================================================================

@router.post("/offer", response_model=DocumentResponse)
async def create_offer(
    offer: OfferCreate,
    db: AsyncSession = Depends(get_db)
):
    """Angebot erstellen"""
    settings = get_settings()
    contact = await get_contact_or_404(db, offer.contact_id)
    
    doc_number = await get_next_number(db, "ANG")
    doc_date = to_datetime(offer.doc_date)
    valid_until = doc_date + timedelta(days=offer.valid_days)
    
    # Positionen als Dict-Liste
    positions = [p.model_dump() for p in offer.positions]
    
    # Kleinunternehmer-Flag aus Config
    kleinunternehmer = settings.sender.kleinunternehmer
    
    # Beträge berechnen
    net_total = sum(p["quantity"] * p["unit_price"] for p in positions)
    if kleinunternehmer:
        vat_total = 0
        gross_total = net_total
    else:
        vat_total = sum(
            p["quantity"] * p["unit_price"] * (p.get("vat_rate", 19) / 100) 
            for p in positions
        )
        gross_total = net_total + vat_total
    
    # Angebote immer mit geschäftlichen Absenderdaten
    sender_data = settings.get_sender("business")
    
    renderer = TypstRenderer()
    
    try:
        pdf_path = renderer.render_offer(
            sender=sender_data,
            contact=contact_to_dict(contact),
            subject=offer.subject,
            positions=positions,
            doc_number=doc_number,
            doc_date=doc_date,
            valid_until=valid_until,
            prepayment_percent=offer.prepayment_percent,
            notes=offer.notes or "",
            kleinunternehmer=kleinunternehmer
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF-Fehler: {str(e)}")
    
    doc = Document(
        doc_type="offer",
        doc_number=doc_number,
        contact_id=contact.id,
        subject=offer.subject,
        positions=positions,
        net_total=net_total,
        vat_total=vat_total,
        gross_total=gross_total,
        doc_date=doc_date,
        valid_until=valid_until,
        status="final",
        pdf_path=str(pdf_path)
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    return doc


# =============================================================================
# ARCHIVIERUNG
# =============================================================================

@router.post("/{doc_id}/archive")
async def archive_to_paperless(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Dokument zu paperless-ngx archivieren"""
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    if not doc.pdf_path:
        raise HTTPException(status_code=400, detail="Kein PDF vorhanden")
    
    pdf_path = Path(doc.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=400, detail="PDF-Datei nicht gefunden")
    
    if doc.status == "archived":
        raise HTTPException(status_code=400, detail="Bereits archiviert")
    
    # Kontakt laden für Korrespondent
    result = await db.execute(
        select(Contact).where(Contact.id == doc.contact_id)
    )
    contact = result.scalar_one_or_none()
    
    correspondent = None
    if contact:
        correspondent = contact.company_name or f"{contact.first_name} {contact.last_name}".strip()
    
    # paperless Client
    client = PaperlessClient()
    if not await client.is_available():
        raise HTTPException(status_code=503, detail="paperless-ngx nicht erreichbar")
    
    # Titel zusammenbauen
    title = doc.doc_number
    if doc.subject:
        title = f"{doc.doc_number} - {doc.subject}"
    
    try:
        task_id = await client.upload_document(
            pdf_path=pdf_path,
            title=title,
            created_date=doc.doc_date.strftime("%Y-%m-%d") if doc.doc_date else None
        )
        
        doc.status = "archived"
        await db.commit()
        
        return {
            "message": "Dokument zur Archivierung übergeben",
            "task_id": task_id,
            "document_id": doc.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Archivierung fehlgeschlagen: {str(e)}"
        )


# =============================================================================
# LÖSCHEN
# =============================================================================

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Dokument löschen"""
    result = await db.execute(
        select(Document).where(Document.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    # PDF-Datei löschen falls vorhanden
    if doc.pdf_path:
        pdf_path = Path(doc.pdf_path)
        if pdf_path.exists():
            pdf_path.unlink()
    
    await db.delete(doc)
    await db.commit()
    
    return {"message": "Dokument gelöscht"}
