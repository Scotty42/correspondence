"""
KI-Endpunkte für Textgenerierung
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Contact
from app.models.schemas import DraftRequest, DraftResponse
from app.services.ollama_client import OllamaClient


router = APIRouter()


@router.post("/draft", response_model=DraftResponse)
async def generate_draft(
    request: DraftRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generiert einen Textentwurf mit KI"""
    client = OllamaClient()
    
    if not await client.is_available():
        raise HTTPException(status_code=503, detail="Ollama nicht erreichbar")
    
    # Kontaktname für Personalisierung
    contact_name = None
    if request.contact_id:
        result = await db.execute(
            select(Contact).where(Contact.id == request.contact_id)
        )
        contact = result.scalar_one_or_none()
        if contact:
            contact_name = contact.company_name or f"{contact.first_name} {contact.last_name}"
    
    try:
        if request.doc_type == "letter":
            text = await client.generate_letter_draft(
                context=request.context,
                tone=request.tone,
                contact_name=contact_name
            )
        elif request.doc_type == "offer_intro":
            text = await client.generate_offer_intro(
                context=request.context,
                contact_name=contact_name
            )
        else:
            text = await client.generate_letter_draft(
                context=request.context,
                tone=request.tone,
                contact_name=contact_name
            )
        
        return DraftResponse(
            text=text.strip(),
            model=client.model
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generierung fehlgeschlagen: {str(e)}")


@router.post("/improve")
async def improve_text(text: str):
    """Verbessert/korrigiert einen Text"""
    client = OllamaClient()
    
    if not await client.is_available():
        raise HTTPException(status_code=503, detail="Ollama nicht erreichbar")
    
    try:
        improved = await client.improve_text(text)
        return {"original": text, "improved": improved.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verbesserung fehlgeschlagen: {str(e)}")
