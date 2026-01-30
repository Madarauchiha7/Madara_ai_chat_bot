import os
import sqlite3
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL")  # private channel ID like -100xxxx

# ================== APP ==================
app = FastAPI()
application = Application.builder().token(BOT_TOKEN).build()

# ================== DATABASE ==================
conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS memory (
    user_id INTEGER,
    key TEXT,
    value TEXT,
    PRIMARY KEY(user_id, key)
)
""")
conn.commit()

# ================== JOIN CHECK ==================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not REQUIRED_CHANNEL:
        return True

    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user.id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass

    await update.message.reply_text("🚨 MUST JOIN OUR CHANNEL")
    return False

# ================== BOT HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_join(update, context):
        return
    await update.message.reply_text("🎉 WELCOME OUR BOT")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_join(update, context):
        return
    await update.message.reply_text("😈 Madara says: " + update.message.text)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ================== FASTAPI LIFECYCLE ==================
@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()

# ================== WEBHOOK ==================
@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "alive"}
