"""
paperless-ngx API Client (korrigiert für Upload)
"""
import httpx
from pathlib import Path
from typing import Optional

from app.settings import get_settings


class PaperlessClient:
    """Client für paperless-ngx Archivierung"""
    
    def __init__(self):
        self.settings = get_settings().paperless
        self.base_url = self.settings.url.rstrip("/")
        self.token = self.settings.api_token
        self.verify_ssl = self.settings.verify_ssl
    
    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Token {self.token}",
            "Accept": "application/json"
        }
    
    @property
    def upload_headers(self) -> dict:
        """Headers für Upload - OHNE Content-Type (wird von httpx gesetzt)"""
        return {
            "Authorization": f"Token {self.token}",
        }
    
    async def is_available(self) -> bool:
        """Prüft ob paperless-ngx erreichbar ist"""
        if not self.settings.enabled or not self.token:
            return False
        try:
            async with httpx.AsyncClient(
                timeout=10,
                verify=self.verify_ssl
            ) as client:
                response = await client.get(
                    f"{self.base_url}/api/documents/",
                    headers=self.headers,
                    params={"page_size": 1}
                )
                return response.status_code in (200, 401, 403)
        except Exception:
            return False
    
    async def upload_document(
        self,
        pdf_path: Path,
        title: str,
        correspondent: Optional[str] = None,
        document_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        created_date: Optional[str] = None
    ) -> str:
        """
        Lädt ein PDF zu paperless-ngx hoch.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            title: Dokumententitel
            correspondent: Name des Korrespondenten (wird ggf. angelegt)
            document_type: Dokumententyp (wird ggf. angelegt)
            tags: Liste von Tags (werden ggf. angelegt)
            created_date: Erstellungsdatum (YYYY-MM-DD)
            
        Returns:
            Task-ID als String
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        
        async with httpx.AsyncClient(
            timeout=60,
            verify=self.verify_ssl
        ) as client:
            # Datei öffnen und als multipart senden
            with open(pdf_path, "rb") as f:
                # Files als tuple: (filename, file_object, content_type)
                files = {
                    "document": (pdf_path.name, f, "application/pdf")
                }
                
                # Form-Daten separat
                data = {"title": title}
                
                if correspondent:
                    data["correspondent"] = correspondent
                if document_type:
                    data["document_type"] = document_type
                if tags:
                    # Tags als komma-separierte Liste ODER mehrere Felder
                    for tag in tags:
                        # paperless erwartet tags als wiederholte Felder
                        pass
                    data["tags"] = ",".join(tags)
                if created_date:
                    data["created"] = created_date
                
                response = await client.post(
                    f"{self.base_url}/api/documents/post_document/",
                    headers=self.upload_headers,  # Ohne Content-Type!
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    raise httpx.HTTPStatusError(
                        f"Upload fehlgeschlagen: {response.status_code} - {response.text}",
                        request=response.request,
                        response=response
                    )
                
                # Response ist die Task-ID als JSON-String
                return response.json()
    
    async def get_task_status(self, task_id: str) -> dict:
        """Prüft den Status eines Upload-Tasks"""
        async with httpx.AsyncClient(
            timeout=10,
            verify=self.verify_ssl
        ) as client:
            response = await client.get(
                f"{self.base_url}/api/tasks/",
                headers=self.headers,
                params={"task_id": task_id}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_correspondents(self) -> list[dict]:
        """Holt alle Korrespondenten"""
        async with httpx.AsyncClient(
            timeout=10,
            verify=self.verify_ssl
        ) as client:
            response = await client.get(
                f"{self.base_url}/api/correspondents/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def get_document_types(self) -> list[dict]:
        """Holt alle Dokumententypen"""
        async with httpx.AsyncClient(
            timeout=10,
            verify=self.verify_ssl
        ) as client:
            response = await client.get(
                f"{self.base_url}/api/document_types/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def get_tags(self) -> list[dict]:
        """Holt alle Tags"""
        async with httpx.AsyncClient(
            timeout=10,
            verify=self.verify_ssl
        ) as client:
            response = await client.get(
                f"{self.base_url}/api/tags/",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("results", [])
