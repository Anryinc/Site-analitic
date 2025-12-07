from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import requests
import logging

load_dotenv()  # loads .env from project root

SUPABASE_REST_URL = os.getenv("SUPABASE_REST_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TABLE = os.getenv("SUPABASE_REST_TABLE", "analytics")

USE_KEY = SERVICE_KEY or ANON_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("site-analytic")

app = FastAPI(title="Site Analytic API")

# serve the static single-page app under /static; keep API routes free
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
def root():
    # serve index.html directly so that SPA is available at '/'
    return FileResponse(os.path.join("static", "index.html"))


@app.get("/api/analytics")
def get_analytics(limit: int = 100):
    """Proxy endpoint that fetches rows from Supabase REST and returns JSON.
    Use `.env` to set `SUPABASE_REST_URL` and `SUPABASE_SERVICE_KEY`.
    """
    if not SUPABASE_REST_URL or not USE_KEY:
        logger.error("Missing SUPABASE_REST_URL or key in .env")
        raise HTTPException(status_code=500, detail="Missing SUPABASE_REST_URL or key in .env")

    url = f"{SUPABASE_REST_URL.rstrip('/')}/rest/v1/{TABLE}"
    headers = {
        "apikey": USE_KEY,
        "Authorization": f"Bearer {USE_KEY}",
        "Accept": "application/json",
    }
    params = {"select": "*", "limit": limit}

    logger.info("Proxying request to Supabase: %s params=%s", url, params)
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.RequestException as e:
        logger.exception("Request to Supabase failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))

    logger.info("Supabase responded: %s", resp.status_code)
    # include a short preview of body for debugging (not for production)
    body_preview = (resp.text[:1000] + '...') if resp.text and len(resp.text) > 1000 else resp.text
    logger.debug("Supabase body preview: %s", body_preview)

    if resp.status_code == 200:
        try:
            return JSONResponse(content=resp.json())
        except Exception as e:
            logger.exception("Failed to decode JSON from Supabase: %s", e)
            return JSONResponse(status_code=500, content={"error": "Invalid JSON from Supabase"})
    else:
        # forward error details when possible
        try:
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        except Exception:
            return JSONResponse(status_code=resp.status_code, content={"error": resp.text})
