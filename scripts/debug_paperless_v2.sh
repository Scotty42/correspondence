#!/bin/bash
# Erweitertes Debug für 302-Redirect Problem

PAPERLESS_URL="http://paperless-ngx.lan.internal:8000"
TOKEN=$(grep "PAPERLESS_API_TOKEN=" /opt/korrespondenz/config/secrets.env 2>/dev/null | cut -d'=' -f2)

echo "=== Redirect-Analyse ==="
echo ""

# 1. Wohin wird umgeleitet?
echo "1. Redirect-Ziel ermitteln..."
curl -s -I "$PAPERLESS_URL/api/" 2>/dev/null | grep -i "location"
echo ""

# 2. Verschiedene API-Endpunkte testen
echo "2. Verschiedene Endpunkte testen..."

for endpoint in "/api/" "/api" "/api/documents/" "/api/token/"; do
    echo -n "   $endpoint → "
    curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Token $TOKEN" \
        "$PAPERLESS_URL$endpoint"
    echo ""
done
echo ""

# 3. Mit -L (Follow Redirects) testen
echo "3. Mit Follow-Redirects (-L)..."
curl -s -L -o /dev/null -w "Final HTTP Status: %{http_code}\n" \
    -H "Authorization: Token $TOKEN" \
    "$PAPERLESS_URL/api/"
echo ""

# 4. Basic Auth Header Format prüfen (manche Versionen brauchen anderen Header)
echo "4. Alternative Auth-Header testen..."

echo -n "   'Token xxx' Format: "
curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Token $TOKEN" \
    "$PAPERLESS_URL/api/"
echo ""

echo -n "   'Bearer xxx' Format: "
curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "$PAPERLESS_URL/api/"
echo ""

# 5. Direkter Request mit voller Ausgabe
echo "5. Vollständiger Request mit Headers..."
echo "   (zeigt Response-Header)"
curl -s -i -H "Authorization: Token $TOKEN" "$PAPERLESS_URL/api/" 2>/dev/null | head -20
echo ""

# 6. Prüfen ob Cookie-basierte Auth erwartet wird
echo "6. Session-Cookie Check..."
echo "   Hole CSRF Token und Session..."
COOKIES=$(curl -s -c - "$PAPERLESS_URL/accounts/login/" 2>/dev/null | grep -E "csrftoken|sessionid")
echo "$COOKIES"
echo ""

# 7. paperless Version ermitteln (wenn möglich)
echo "7. paperless-ngx Version..."
curl -s -L "$PAPERLESS_URL/api/ui_settings/" 2>/dev/null | head -c 500
echo ""
echo ""

echo "=== Ende erweiterte Analyse ==="
