from authlib.integrations.base_client.errors import OAuthError
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Query, Request

from app.auth.jwt import create_access_token
from app.core.config import settings

router = APIRouter()

oauth = OAuth()


def _ensure_google_oauth_configured():
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured (missing client id/secret)")
    if not settings.google_redirect_uri:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured (missing redirect uri)")


def _get_google_client():
    _ensure_google_oauth_configured()

    # Lazy register allows env changes without code reload.
    if not hasattr(oauth, "google"):
        oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    return oauth.google


@router.get("/google/login")
async def google_login(request: Request, redirect_to: str = Query(default="")):
    google = _get_google_client()
    if redirect_to:
        request.session["redirect_to"] = redirect_to
    return await google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, redirect_to: str = Query(default="/")):
    try:
        google = _get_google_client()
        token = await google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = await google.userinfo(token=token)

        sub = userinfo.get("sub") or userinfo.get("id")
        email = userinfo.get("email")
        if not sub:
            raise HTTPException(status_code=400, detail="Unable to read Google user id")

        access_token = create_access_token(subject=str(sub), email=email)

        # For quick manual testing: redirect back with token in query string.
        # In production, prefer HttpOnly cookies or a front-end token exchange.
        if not redirect_to or redirect_to == "/":
            redirect_to = request.session.pop("redirect_to", redirect_to) or redirect_to

        url = f"{redirect_to}"
        sep = "&" if "?" in url else "?"
        return RedirectResponse(url=f"{url}{sep}token={access_token}")
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {e.error}") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Google OAuth callback failed") from e


@router.get("/me")
def me(request: Request):
    # Useful to see if auth is configured; actual JWT protection is on PO APIs.
    return {"auth": "google-oauth", "configured": bool(settings.google_client_id and settings.google_client_secret)}

