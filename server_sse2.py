import asyncio
import os
import json
import base64
from pathlib import Path
from email.mime.text import MIMEText
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

# ✅ Google API imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# =========================================================
# 🔐 CONFIGURATION & SECRETS
# =========================================================
load_dotenv()

EXPECTED_TOKEN = os.getenv("MCP_API_TOKEN")
if not EXPECTED_TOKEN:
    raise ValueError("❌ MCP_API_TOKEN non défini dans .env")

# =========================================================
# 📧 GMAIL AUTH (Version Refresh Token Direct)
# =========================================================
def get_gmail_service():
    """Authentification via Refresh Token (Idéal pour les serveurs)"""
    creds = Credentials(
        token=None,  # Le token d'accès sera généré automatiquement
        refresh_token=os.getenv("GOOGLE_WORKSPACE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_WORKSPACE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_WORKSPACE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build('gmail', 'v1', credentials=creds)

# =========================================================
# 🚀 MCP SERVER & TOOLS
# =========================================================
mcp = FastMCP("Google-Workspace-Secure-SSE")

@mcp.tool()
async def gmail_list_messages(max_results: int = 5):
    """Liste les derniers emails Gmail"""
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return "📭 Aucun message trouvé."
        
        email_list = []
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id'], format='metadata', 
                                              metadataHeaders=['From', 'Subject']).execute()
            headers = {h['name']: h['value'] for h in m['payload']['headers']}
            email_list.append(f"- De: {headers.get('From')}\n  Objet: {headers.get('Subject')}")
            
        return "📧 Derniers emails :\n" + "\n".join(email_list)
    except Exception as e:
        return f"❌ Erreur : {str(e)}"

@mcp.tool()
async def gmail_send_email(to: str, subject: str, body: str):
    """Envoie un email réel via Gmail API"""
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_msg = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        
        return f"✅ Email envoyé avec succès à {to} (ID: {sent_msg['id']})"
    except HttpError as error:
        # C'est ici que tu verras l'erreur 511 si l'adresse est mauvaise
        return f"❌ Erreur API Google (Vérifiez l'adresse destinataire) : {error}"
    except Exception as e:
        return f"❌ Erreur : {str(e)}"

# =========================================================
# 🔐 AUTH MIDDLEWARE (ASGI PUR)
# =========================================================
class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if path == "/health":
            await self.app(scope, receive, send)
            return

        if path.startswith("/sse") or path.startswith("/messages"):
            headers = dict(scope.get("headers", []))
            # Récupération sécurisée du header authorization
            auth_header = headers.get(b"authorization", b"").decode()

            if not auth_header.startswith("Bearer ") or auth_header.replace("Bearer ", "") != EXPECTED_TOKEN:
                print(f"🚫 Accès bloqué pour {path}: Token invalide ou manquant")
                response = JSONResponse({"error": "Unauthorized"}, status_code=403)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

# =========================================================
# 🌐 STARLETTE APP
# =========================================================
async def health(request):
    return JSONResponse({"status": "ok"})

sse_app = mcp.sse_app()
base_app = Starlette(routes=[Route("/health", health)])
base_app.mount("/", sse_app)

# Application du verrou de sécurité
app = AuthMiddleware(base_app)

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 SERVEUR MCP SSE SÉCURISÉ ACTIF")
    print(f"📡 Endpoint: http://localhost:8000/sse")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)