# Smart Planning Auto-Corrector - Schnellstart

## 1. Token holen

```powershell
# Führe get_token.ps1 aus
.\get_token.ps1

# Token wird automatisch in Zwischenablage kopiert
# Gültig für ~5 Minuten
```

## 2. Snapshot korrigieren

```bash
# Mit Token aus Zwischenablage (Strg+V)
python main_correction.py example_snapshots/snapshot-1/Snapshot-Inhalt.json \
    --bearer-token "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
    --openai-key "sk-..." \
    --output snapshot_corrected.json \
    --log correction_log.json

# Mit allen Optionen
python main_correction.py snapshot.json \
    --bearer-token "eyJhbGc..." \
    --api-url "https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/esarom-be/api/v1" \
    --openai-key "sk-..." \
    --model gpt-4o-mini \
    --max-iterations 10 \
    --output corrected.json \
    --log log.json

# Mit SSL-Verifikation (Produktion)
python main_correction.py snapshot.json \
    --bearer-token "eyJhbGc..." \
    --verify-ssl \
    --openai-key "sk-..."
```

## API Details

**Base URL (Test):**
```
https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/esarom-be/api/v1
```

**Keycloak Token Endpoint:**
```
https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/keycloak/realms/Esarom/protocol/openid-connect/token
```

**Client Credentials:**
- client_id: `apiClient-test`
- client_secret: `UDgRYjOcMkFzQonSfBZI9VYvCuuC9PZA`

## Token Ablauf

- Token läuft nach ~5 Minuten ab
- Bei Error 401: Neuen Token holen mit `.\get_token.ps1`
- Für längere Sessions: Token regelmäßig erneuern

## Tipps

**Token in Variable speichern (PowerShell):**
```powershell
$token = (.\get_token.ps1)[0]  # Erste Zeile = Token
python main_correction.py snapshot.json --bearer-token "$token" --openai-key "sk-..."
```

**OpenAI Key aus .env:**
```bash
# .env erstellen
OPENAI_API_KEY=sk-...

# Python lädt automatisch aus .env
```

**Nur Token anzeigen (ohne Kopieren):**
```powershell
# Token-Response direkt
$response = Invoke-RestMethod -Method POST `
  -Uri "https://vm-t-weu-ccadmm-idp-test02.internal.idp.cca-dev.com/keycloak/realms/Esarom/protocol/openid-connect/token" `
  -Headers @{ "Content-Type" = "application/x-www-form-urlencoded" } `
  -Body @{
    client_id     = "apiClient-test"
    client_secret = "UDgRYjOcMkFzQonSfBZI9VYvCuuC9PZA"
    grant_type    = "client_credentials"
  }

Write-Host $response.access_token
```
