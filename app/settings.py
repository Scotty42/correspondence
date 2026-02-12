"""
Konfigurationsmanagement für das Korrespondenz-System
"""
"""
Configuration design:
- YAML files define structural configuration
- secrets.env is loaded explicitly for credentials
- Environment variables override YAML only where explicitly applied
- Nested config uses BaseModel (not BaseSettings) to avoid implicit env loading
"""
from pathlib import Path
from functools import lru_cache

from pydantic import BaseModel, Field, AliasChoices, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict 

import yaml

import os
from dotenv import load_dotenv

class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    log_level: str = "info"


class DatabaseSettings(BaseModel):
    # allow overriding via env var KORRESPONDENZ_DATABASE_URL
    #url: str = Field(
    #    default="sqlite+aiosqlite:////opt/korrespondenz/data/korrespondenz.sqlite",
    #    validation_alias="KORRESPONDENZ_DATABASE_URL",
    #)
    url: str = "sqlite+aiosqlite:///data/korrespondenz.sqlite"
    model_config = ConfigDict(extra="forbid")


class TypstSettings(BaseModel):
    binary: str = "/usr/local/bin/typst"
    cache_dir: str = "/opt/korrespondenz/.typst-cache"
    templates_dir: str = "/opt/korrespondenz/templates"
    output_dir: str = "/opt/korrespondenz/data/documents"


class PaperlessSettings(BaseModel):
    enabled: bool = True
    url: str = "http://paperless-ngx.lan.internal:8000"
    api_token: str = ""   # value injected in from_yaml()
    verify_ssl: bool = False


class OllamaSettings(BaseModel):
    enabled: bool = True
    url: str = "http://ollama.lan.internal:11434"
    model: str = "gemma2-small-ctx:latest"
    timeout: int = 120


class SenderAddress(BaseModel):
    street: str = ""
    zip: str = ""
    city: str = ""
    country: str = "Deutschland"


class SenderContact(BaseModel):
    phone: str = ""
    email: str = ""
    website: str = ""


class SenderContactPrivate(BaseModel):
    """Kontaktdaten für Privatperson (ohne Website)"""
    phone: str = ""
    email: str = ""


class SenderBank(BaseModel):
    iban: str = ""
    bic: str = ""
    bank_name: str = ""


class SenderTax(BaseModel):
    ustid: str = ""
    steuernummer: str = ""


class SenderSettings(BaseModel):
    """Geschäftliche Absenderdaten"""
    name: str = ""
    address: SenderAddress = SenderAddress()
    contact: SenderContact = SenderContact()
    bank: SenderBank = SenderBank()
    tax: SenderTax = SenderTax()
    kleinunternehmer: bool = False


class SenderPrivateSettings(BaseModel):
    """Private Absenderdaten"""
    name: str = ""
    address: SenderAddress = SenderAddress()
    contact: SenderContactPrivate = SenderContactPrivate()


class Settings(BaseSettings):
    """Hauptkonfiguration - lädt aus config.yaml"""
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    typst: TypstSettings = Field(default_factory=TypstSettings)
    paperless: PaperlessSettings = Field(default_factory=PaperlessSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    sender: SenderSettings = Field(default_factory=SenderSettings)
    sender_private: SenderPrivateSettings = Field(default_factory=SenderPrivateSettings)
   
    @classmethod
    def from_yaml(cls, path: str = "/opt/korrespondenz/config/config.yaml"):
        config_path = Path(path)
        data: dict = {}

        if config_path.exists():
            data = yaml.safe_load(config_path.read_text()) or {}

        # Support legacy shorthand: database: "<url>"
        db = data.get("database")
        if isinstance(db, str):
            data["database"] = {"url": db}
        elif db is None:
            data["database"] = {}

        # Load secrets.env into process env (optional)
        secrets_path = Path("/opt/korrespondenz/config/secrets.env")
        if secrets_path.exists():
            load_dotenv(secrets_path, override=False)

        # IMPORTANT: validate dict as a model (no settings sources)
        settings = cls.model_validate(data)

        # Explicit env overrides (CI/smoke)
        db_url = os.getenv("KORRESPONDENZ_DATABASE_URL")
        if db_url:
            settings.database.url = db_url

        return settings

    def get_sender(self, letter_type: str = "business") -> dict:
        """
        Gibt die passenden Absenderdaten zurück.
        
        Args:
            letter_type: "business" oder "private"
            
        Returns:
            Dict mit Absenderdaten
        """
        if letter_type == "private":
            return self.sender_private.model_dump()
        return self.sender.model_dump()


@lru_cache
def get_settings() -> Settings:
    """Cached Settings-Instanz"""
    return Settings.from_yaml()
