"""
Pydantic Schemas für API Request/Response
"""
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


# === Kontakte ===

class ContactBase(BaseModel):
    contact_type: str = "company"
    company_name: Optional[str] = None
    salutation: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    street: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "Deutschland"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    customer_number: Optional[str] = None
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# === Positionen (für Rechnungen/Angebote) ===

class Position(BaseModel):
    description: str
    quantity: float = 1.0
    unit: str = "Stück"
    unit_price: float
    vat_rate: float = 19.0
    
    @property
    def net_amount(self) -> float:
        return self.quantity * self.unit_price
    
    @property
    def vat_amount(self) -> float:
        return self.net_amount * (self.vat_rate / 100)
    
    @property
    def gross_amount(self) -> float:
        return self.net_amount + self.vat_amount


# === Dokumente ===

class LetterCreate(BaseModel):
    """Brief erstellen"""
    contact_id: int
    subject: str
    content: str
    letter_type: Literal["business", "private"] = "business"
    doc_date: Optional[date] = None


class InvoiceCreate(BaseModel):
    """Rechnung erstellen"""
    contact_id: int
    positions: list[Position]
    doc_date: Optional[date] = None
    due_days: int = 14  # Zahlungsziel in Tagen
    notes: Optional[str] = None


class OfferCreate(BaseModel):
    """Angebot erstellen"""
    contact_id: int
    subject: str
    positions: list[Position]
    doc_date: Optional[date] = None
    valid_days: int = 30  # Gültigkeit in Tagen
    prepayment_percent: Optional[float] = None
    notes: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    doc_type: str
    doc_number: str
    contact_id: int
    subject: Optional[str]
    status: str
    net_total: Optional[float]
    gross_total: Optional[float]
    doc_date: datetime
    pdf_path: Optional[str]
    paperless_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# === AI ===

class DraftRequest(BaseModel):
    """Anfrage für KI-generierten Entwurf"""
    doc_type: str = "letter"  # letter, invoice_note, offer_intro
    context: str  # Beschreibung des Anliegens
    tone: str = "formal"  # formal, friendly
    letter_type: Literal["business", "private"] = "business"
    contact_id: Optional[int] = None  # Für Personalisierung


class DraftResponse(BaseModel):
    """Antwort mit generiertem Text"""
    text: str
    model: str
    tokens_used: Optional[int] = None
