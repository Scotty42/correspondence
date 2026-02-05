#!/bin/bash
# Debug-Script für paperless-ngx Verbindung
# Auf dem Korrespondenz-LXC ausführen

echo "=== paperless-ngx Debug ==="
echo ""

PAPERLESS_URL="http://paperless-ngx.lan.internal:8000"

# 1. Basis-Erreichbarkeit
echo "1. Basis-Erreichbarkeit testen..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$PAPERLESS_URL"
echo ""

# 2. API-Root ohne Auth
echo "2. API-Root ohne Auth..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$PAPERLESS_URL/api/"
echo ""

# 3. Secrets-Datei prüfen
echo "3. Secrets-Datei prüfen..."
if [ -f /opt/korrespondenz/config/secrets.env ]; then
    echo "   secrets.env existiert"
    grep -q "PAPERLESS_API_TOKEN=" /opt/korrespondenz/config/secrets.env && echo "   Token-Variable vorhanden" || echo "   FEHLER: Token-Variable fehlt"
    
    # Token extrahieren (ohne Wert anzuzeigen)
    TOKEN=$(grep "PAPERLESS_API_TOKEN=" /opt/korrespondenz/config/secrets.env | cut -d'=' -f2)
    if [ -z "$TOKEN" ] || [ "$TOKEN" = "your_token_here" ]; then
        echo "   FEHLER: Token ist leer oder Platzhalter!"
    else
        echo "   Token ist gesetzt (Länge: ${#TOKEN} Zeichen)"
    fi
else
    echo "   FEHLER: secrets.env nicht gefunden!"
fi
echo ""

# 4. API mit Token testen (falls Token gesetzt)
echo "4. API mit Token testen..."
TOKEN=$(grep "PAPERLESS_API_TOKEN=" /opt/korrespondenz/config/secrets.env 2>/dev/null | cut -d'=' -f2)
if [ -n "$TOKEN" ] && [ "$TOKEN" != "your_token_here" ]; then
    echo "   Request: GET $PAPERLESS_URL/api/"
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -H "Authorization: Token $TOKEN" \
        -H "Accept: application/json" \
        "$PAPERLESS_URL/api/")
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE:/d')
    
    echo "   HTTP Status: $HTTP_CODE"
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ API erreichbar!"
        echo "   Response (gekürzt): $(echo $BODY | head -c 200)..."
    else
        echo "   ❌ API-Fehler"
        echo "   Response: $BODY"
    fi
else
    echo "   ⚠️  Übersprungen - kein Token konfiguriert"
fi
echo ""

# 5. Python-Client direkt testen
echo "5. Python-Client testen..."
cd /opt/korrespondenz
source .venv/bin/activate

python3 << 'PYEOF'
import asyncio
from app.settings import get_settings
from app.services.paperless_client import PaperlessClient

async def test():
    settings = get_settings()
    print(f"   URL: {settings.paperless.url}")
    print(f"   Token gesetzt: {bool(settings.paperless.api_token)}")
    print(f"   Token-Länge: {len(settings.paperless.api_token)} Zeichen")
    
    client = PaperlessClient()
    available = await client.is_available()
    print(f"   is_available(): {available}")

asyncio.run(test())
PYEOF

echo ""
echo "=== Ende Debug ==="
