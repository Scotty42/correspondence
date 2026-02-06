"""
Konfigurationsmanagement für das Korrespondenz-System
"""
from pathlib import Path
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import os

class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    log_level: str = "info"


class DatabaseSettings(BaseSettings):
    # allow overriding via env var KORRESPONDENZ_DATABASE_URL
    url: str = Field(
        default="sqlite+aiosqlite:///data/korrespondenz.sqlite",
        validation_alias="KORRESPONDENZ_DATABASE_URL",
    )


class TypstSettings(BaseSettings):
    binary: str = "/usr/local/bin/typst"
    cache_dir: str = "/opt/korrespondenz/.typst-cache"
    templates_dir: str = "/opt/korrespondenz/templates"
    output_dir: str = "/opt/korrespondenz/data/documents"


class PaperlessSettings(BaseSettings):
    enabled: bool = True
    url: str = "http://paperless-ngx.lan.internal:8000"
    api_token: str = Field(default="", alias="PAPERLESS_API_TOKEN")
    verify_ssl: bool = False
    
    model_config = SettingsConfigDict(
        env_file="/opt/korrespondenz/config/secrets.env",
        extra="ignore"
    )


class OllamaSettings(BaseSettings):
    enabled: bool = True
    url: str = "http://ollama.lan.internal:11434"
    model: str = "gemma2-small-ctx:latest"
    timeout: int = 120


class SenderAddress(BaseSettings):
    street: str = ""
    zip: str = ""
    city: str = ""
    country: str = "Deutschland"


class SenderContact(BaseSettings):
    phone: str = ""
    email: str = ""
    website: str = ""


class SenderContactPrivate(BaseSettings):
    """Kontaktdaten für Privatperson (ohne Website)"""
    phone: str = ""
    email: str = ""


class SenderBank(BaseSettings):
    iban: str = ""
    bic: str = ""
    bank_name: str = ""


class SenderTax(BaseSettings):
    ustid: str = ""
    steuernummer: str = ""


class SenderSettings(BaseSettings):
    """Geschäftliche Absenderdaten"""
    name: str = ""
    address: SenderAddress = SenderAddress()
    contact: SenderContact = SenderContact()
    bank: SenderBank = SenderBank()
    tax: SenderTax = SenderTax()
    kleinunternehmer: bool = False


class SenderPrivateSettings(BaseSettings):
    """Private Absenderdaten"""
    name: str = ""
    address: SenderAddress = SenderAddress()
    contact: SenderContactPrivate = SenderContactPrivate()


class Settings(BaseSettings):
    """Hauptkonfiguration - lädt aus config.yaml"""
    server: ServerSettings = ServerSettings()
    database: DatabaseSettings = DatabaseSettings()
    typst: TypstSettings = TypstSettings()
    paperless: PaperlessSettings = PaperlessSettings()
    ollama: OllamaSettings = OllamaSettings()
    sender: SenderSettings = SenderSettings()
    sender_private: SenderPrivateSettings = SenderPrivateSettings()
    
    @classmethod
    def from_yaml(cls, path: str = "/opt/korrespondenz/config/config.yaml"):
        """Lädt Konfiguration aus YAML-Datei und überschreibt mit ENV wenn gesetzt"""
        config_path = Path(path)
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
                settings = cls(**data)
        else:
            settings = cls()

        # ENV overrides (CI / smoke)
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
