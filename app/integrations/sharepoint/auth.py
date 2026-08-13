# integrations/sharepoint/auth.py
import msal
from app.core.config import settings

_app = msal.ConfidentialClientApplication(
    client_id=settings.AZURE_CLIENT_ID,
    client_credential=settings.AZURE_CLIENT_SECRET,
    authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
)

def get_graph_token() -> str:
    result = _app.acquire_token_silent(scopes=["https://graph.microsoft.com/.default"], account=None)
    if not result:
        result = _app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return result["access_token"]