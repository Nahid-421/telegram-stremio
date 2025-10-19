from fastapi import FastAPI, Request, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os, httpx
from pymongo import MongoClient

load_dotenv()
app = FastAPI()

BASE_URL = os.getenv("BASE_URL")
DATABASE = os.getenv("DATABASE").split(",")[0]  # connect to first MongoDB URI
client = MongoClient(DATABASE)
db = client["stremio"]
files_col = db["files"]

@app.get("/stream/{file_id}")
async def stream(file_id: str, range: str = Header(None), token: str = None):
    file_doc = files_col.find_one({"file_id": file_id})
    if not file_doc or file_doc.get("token") != token:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    tg_file_path = file_doc["file_path"]
    tg_url = f"https://api.telegram.org/file/bot{os.getenv('BOT_TOKEN')}/{tg_file_path}"
    headers = {}
    if range:
        headers["Range"] = range
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(tg_url, headers=headers, timeout=60)
        response_headers = {
            "Content-Type": resp.headers.get("Content-Type", "video/mp4"),
            "Accept-Ranges": "bytes",
        }
        if "Content-Range" in resp.headers:
            response_headers["Content-Range"] = resp.headers["Content-Range"]
        if "Content-Length" in resp.headers:
            response_headers["Content-Length"] = resp.headers["Content-Length"]
        return Response(content=resp.content, status_code=resp.status_code, headers=response_headers)

@app.get("/stremio/manifest.json")
def manifest():
    return JSONResponse({
        "id": "org.telegram.stremio",
        "name": "Telegram Stremio Addon",
        "description": "Stream your Telegram channel media directly on Stremio",
        "types": ["movie","series"],
        "catalogs": [{"type":"movie","id":"movies"},{"type":"series","id":"tv"}],
        "resources":["catalog","meta","stream"]
    })

@app.get("/stremio/catalog/{catalog_id}.json")
def catalog(catalog_id: str):
    items = []
    for doc in files_col.find({"type": catalog_id}):
        items.append({
            "id": doc["file_id"],
            "name": doc["name"],
            "poster": doc.get("poster",""),
            "type": catalog_id
        })
    return {"metas": items}

@app.get("/stremio/meta/{file_id}.json")
def meta(file_id: str):
    doc = files_col.find_one({"file_id": file_id})
    if not doc:
        raise HTTPException(404,"Not Found")
    return {
        "id": doc["file_id"],
        "name": doc["name"],
        "type": doc["type"],
        "stream": [{"url": f"{BASE_URL}/stream/{doc['file_id']}?token={doc['token']}","name":"Telegram Stream"}]
    }
