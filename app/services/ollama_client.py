"""
Ollama LLM Client für Textgenerierung
"""
import httpx
from typing import Optional

from app.settings import get_settings


class OllamaClient:
    """Client für lokale Ollama-Instanz"""
    
    def __init__(self):
        self.settings = get_settings().ollama
        self.base_url = self.settings.url.rstrip("/")
        self.model = self.settings.model
        self.timeout = self.settings.timeout
    
    async def is_available(self) -> bool:
        """Prüft ob Ollama erreichbar ist"""
        if not self.settings.enabled:
            return False
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generiert Text mit Ollama.
        
        Args:
            prompt: User-Prompt
            system: System-Prompt (optional)
            temperature: Kreativität (0.0-1.0)
            
        Returns:
            Generierter Text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json()["response"]
    
    async def generate_letter_draft(
        self,
        context: str,
        tone: str = "formal",
        contact_name: Optional[str] = None
    ) -> str:
        """Generiert einen Briefentwurf"""
        
        system = """Du bist ein Assistent für deutsche Geschäftskorrespondenz.
Du schreibst professionelle, klare und höfliche Brieftexte.
Antworte NUR mit dem Brieftext selbst - OHNE Anrede und OHNE Grußformel.
Diese werden automatisch vom System ergänzt.
Halte dich kurz und präzise. Verwende keine Floskeln."""

        prompt = f"""Schreibe einen {tone}en Brieftext für folgendes Anliegen:

{context}

{"Empfänger: " + contact_name if contact_name else ""}

Brieftext (ohne Anrede/Gruß):"""

        return await self.generate(prompt, system, temperature=0.5)
    
    async def generate_offer_intro(
        self,
        context: str,
        contact_name: Optional[str] = None
    ) -> str:
        """Generiert Einleitungstext für ein Angebot"""
        
        system = """Du bist ein Assistent für deutsche Geschäftskorrespondenz.
Du schreibst professionelle Angebotstexte.
Der Text soll das Angebot einleiten und den Kunden überzeugen.
Antworte NUR mit dem Einleitungstext - kurz und überzeugend."""

        prompt = f"""Schreibe einen Einleitungstext für ein Angebot zu:

{context}

{"Kunde: " + contact_name if contact_name else ""}

Einleitungstext:"""

        return await self.generate(prompt, system, temperature=0.6)
    
    async def improve_text(self, text: str) -> str:
        """Verbessert/korrigiert einen Text"""
        
        system = """Du bist ein Lektor für deutsche Geschäftskorrespondenz.
Korrigiere Rechtschreibung, Grammatik und Stil.
Behalte den ursprünglichen Inhalt und Ton bei.
Antworte NUR mit dem korrigierten Text."""

        prompt = f"""Korrigiere und verbessere folgenden Text:

{text}

Korrigierter Text:"""

        return await self.generate(prompt, system, temperature=0.3)
