from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
import os
import requests
import logging

load_dotenv()

SUPABASE_REST_URL = os.getenv("SUPABASE_REST_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TABLE = os.getenv("SUPABASE_REST_TABLE", "Analytics")

USE_KEY = SERVICE_KEY or ANON_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("site-analytic")

app = FastAPI(title="Site Analytic API")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join("static", "index.html"))

class Positions(BaseModel):
    vacancy_category: str
    positions: dict  # {"intern": 60, "junior": 140, ...}

@app.post("/api/save_positions")
def save_positions(pos: Positions):
    if not SUPABASE_REST_URL or not USE_KEY:
        raise HTTPException(status_code=500, detail="Missing Supabase config")

    url = f"{SUPABASE_REST_URL}/rest/v1/{TABLE}"
    headers = {
        "apikey": USE_KEY,
        "Authorization": f"Bearer {USE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    # Update row by vacancy_category
    update_data = {"grades_positions": pos.positions}
    params = {"vacancy_category": f"eq.{pos.vacancy_category}"}

    logger.info("Updating positions for %s", pos.vacancy_category)
    try:
        resp = requests.patch(url, headers=headers, json=update_data, params=params, timeout=15)
    except requests.RequestException as e:
        logger.exception("Request to Supabase failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e))

    if resp.status_code == 204 or resp.status_code == 200:
        return {"success": true}
    else:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

@app.get("/api/analytics")
def get_analytics(limit: int = 100):
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
    body_preview = (resp.text[:1000] + '...') if resp.text and len(resp.text) > 1000 else resp.text
    logger.debug("Supabase body preview: %s", body_preview)

    if resp.status_code == 200:
        try:
            return JSONResponse(content=resp.json())
        except Exception as e:
            logger.exception("Failed to decode JSON from Supabase: %s", e)
            return JSONResponse(status_code=500, content={"error": "Invalid JSON from Supabase"})
    else:
        try:
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        except Exception:
            return JSONResponse(status_code=resp.status_code, content={"error": resp.text})
