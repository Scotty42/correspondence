"""
Typst PDF-Rendering Service
"""
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Any

from app.settings import get_settings


class TypstRenderer:
    """Rendert Typst-Templates zu PDF"""
    
    def __init__(self):
        self.settings = get_settings()
        self.typst_bin = self.settings.typst.binary
        self.templates_dir = Path(self.settings.typst.templates_dir)
        self.output_dir = Path(self.settings.typst.output_dir)
        self.cache_dir = self.settings.typst.cache_dir
        
        # Output-Verzeichnis sicherstellen
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def render(
        self,
        template_name: str,
        data: dict[str, Any],
        output_filename: str
    ) -> Path:
        """
        Rendert ein Template mit den gegebenen Daten zu PDF.
        
        Args:
            template_name: Name des Templates (z.B. "letter/default.typ")
            data: Daten für das Template
            output_filename: Name der Ausgabedatei (ohne .pdf)
            
        Returns:
            Pfad zur generierten PDF-Datei
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template nicht gefunden: {template_path}")
        
        output_path = self.output_dir / f"{output_filename}.pdf"
        
        # Daten als JSON - im selben Verzeichnis wie das Template
        template_dir = template_path.parent
        data_file_path = template_dir / "_data.json"
        
        try:
            # JSON-Daten schreiben
            with open(data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, default=str, indent=2)
            
            # Umgebungsvariablen
            env = os.environ.copy()
            env["TYPST_CACHE_DIR"] = self.cache_dir
            
            # Typst kompilieren
            result = subprocess.run(
                [
                    self.typst_bin,
                    "compile",
                    "--root", str(self.templates_dir),
                    str(template_path),
                    str(output_path)
                ],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(template_dir)
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Typst-Fehler: {result.stderr}")
            
            return output_path
            
        finally:
            # Temp-Datei aufräumen
            if data_file_path.exists():
                data_file_path.unlink()
    
    def render_letter(
        self,
        sender: dict,
        contact: dict,
        subject: str,
        content: str,
        doc_number: str,
        doc_date: datetime,
        letter_type: str = "business"
    ) -> Path:
        """Rendert einen Geschäfts- oder Privatbrief"""
        data = {
            "sender": sender,
            "contact": contact,
            "subject": subject,
            "content": content,
            "doc_number": doc_number,
            "doc_date": doc_date.strftime("%d.%m.%Y"),
            "letter_type": letter_type
        }
        
        prefix = "brief" if letter_type == "business" else "privat"
        filename = f"{prefix}_{doc_number}_{doc_date.strftime('%Y%m%d')}"
        return self.render("letter/default.typ", data, filename)
    
    def render_invoice(
        self,
        sender: dict,
        contact: dict,
        positions: list[dict],
        doc_number: str,
        doc_date: datetime,
        due_date: datetime,
        notes: str = "",
        kleinunternehmer: bool = False
    ) -> Path:
        """Rendert eine Rechnung"""
        # Beträge berechnen
        net_total = sum(p["quantity"] * p["unit_price"] for p in positions)
        
        if kleinunternehmer:
            vat_total = 0
            gross_total = net_total
        else:
            vat_amounts = {}
            for p in positions:
                rate = p.get("vat_rate", 19)
                amount = p["quantity"] * p["unit_price"] * (rate / 100)
                vat_amounts[rate] = vat_amounts.get(rate, 0) + amount
            vat_total = sum(vat_amounts.values())
            gross_total = net_total + vat_total
        
        # Kleinunternehmer-Flag in Sender-Daten einbetten
        sender_with_flag = {**sender, "kleinunternehmer": kleinunternehmer}
        
        data = {
            "sender": sender_with_flag,
            "contact": contact,
            "positions": positions,
            "doc_number": doc_number,
            "doc_date": doc_date.strftime("%d.%m.%Y"),
            "due_date": due_date.strftime("%d.%m.%Y"),
            "net_total": net_total,
            "vat_total": vat_total,
            "gross_total": gross_total,
            "notes": notes
        }
        
        filename = f"rechnung_{doc_number}_{doc_date.strftime('%Y%m%d')}"
        return self.render("invoice/default.typ", data, filename)
    
    def render_offer(
        self,
        sender: dict,
        contact: dict,
        subject: str,
        positions: list[dict],
        doc_number: str,
        doc_date: datetime,
        valid_until: datetime,
        prepayment_percent: float = None,
        notes: str = "",
        kleinunternehmer: bool = False
    ) -> Path:
        """Rendert ein Angebot"""
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
        
        # Kleinunternehmer-Flag in Sender-Daten einbetten
        sender_with_flag = {**sender, "kleinunternehmer": kleinunternehmer}
        
        data = {
            "sender": sender_with_flag,
            "contact": contact,
            "subject": subject,
            "positions": positions,
            "doc_number": doc_number,
            "doc_date": doc_date.strftime("%d.%m.%Y"),
            "valid_until": valid_until.strftime("%d.%m.%Y"),
            "net_total": net_total,
            "vat_total": vat_total,
            "gross_total": gross_total,
            "prepayment_percent": prepayment_percent,
            "notes": notes
        }
        
        filename = f"angebot_{doc_number}_{doc_date.strftime('%Y%m%d')}"
        return self.render("offer/default.typ", data, filename)
