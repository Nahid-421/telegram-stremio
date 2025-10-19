from pyrogram import Client, filters
from pymongo import MongoClient
import os
from utils import generate_token, parse_caption

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTH_CHANNEL = os.getenv("AUTH_CHANNEL").split(",")
DATABASE = os.getenv("DATABASE").split(",")[0]

db = MongoClient(DATABASE)["stremio"]
files_col = db["files"]

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.chat(AUTH_CHANNEL) & (filters.document | filters.video))
def handle_file(client, message):
    file_id = str(message.message_id)
    token = generate_token()
    file_path = client.get_file(message).file_path
    caption = message.caption or ""
    meta = parse_caption(caption)
    
    doc = {
        "file_id": file_id,
        "chat_id": message.chat.id,
        "file_path": file_path,
        "token": token,
        "name": meta.get("name", f"File {file_id}"),
        "type": "movie",  # optionally detect TV series
        "quality": meta.get("quality","Unknown")
    }
    files_col.update_one({"file_id": file_id},{"$set": doc},upsert=True)
    
    link = f"{os.getenv('BASE_URL')}/stream/{file_id}?token={token}"
    message.reply_text(f"✅ Stream link:\n{link}")

app.run()
