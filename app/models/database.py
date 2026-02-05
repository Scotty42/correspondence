"""
SQLAlchemy Datenbankmodelle
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Contact(Base):
    """Kontakt/Empfänger"""
    __tablename__ = "contacts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Typ
    contact_type: Mapped[str] = mapped_column(String(20), default="company")  # company, person
    
    # Firma
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Person
    salutation: Mapped[Optional[str]] = mapped_column(String(20))  # Herr, Frau, etc.
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[Optional[str]] = mapped_column(String(1))  # m, f, d
    
    # Adresse
    street: Mapped[Optional[str]] = mapped_column(String(255))
    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Deutschland")
    
    # Kontakt
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Referenzen
    customer_number: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Meta
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Beziehungen
    documents: Mapped[list["Document"]] = relationship(back_populates="contact")


class Document(Base):
    """Erstelltes Dokument"""
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Typ und Nummer
    doc_type: Mapped[str] = mapped_column(String(20))  # letter, invoice, offer
    doc_number: Mapped[str] = mapped_column(String(50), unique=True)
    
    # Empfänger
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"))
    contact: Mapped["Contact"] = relationship(back_populates="documents")
    
    # Inhalt
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    content: Mapped[Optional[str]] = mapped_column(Text)  # Freitext für Briefe
    positions: Mapped[Optional[dict]] = mapped_column(JSON)  # Positionen für Rechnungen/Angebote
    
    # Beträge (für Rechnungen/Angebote)
    net_total: Mapped[Optional[float]] = mapped_column(Float)
    vat_total: Mapped[Optional[float]] = mapped_column(Float)
    gross_total: Mapped[Optional[float]] = mapped_column(Float)
    
    # Daten
    doc_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)  # Fälligkeitsdatum
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime)  # Für Angebote
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, final, sent, archived
    
    # Dateien
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))
    paperless_id: Mapped[Optional[int]] = mapped_column(Integer)  # ID in paperless-ngx
    
    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NumberSequence(Base):
    """Nummernkreise für Dokumente"""
    __tablename__ = "number_sequences"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(String(20), unique=True)  # INV, OFF, LTR
    year: Mapped[int] = mapped_column(Integer)
    last_number: Mapped[int] = mapped_column(Integer, default=0)
