import os
import random
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ─── CONFIG ────────────────────────────────────────
TOKEN = os.getenv("TOKEN", "").strip()
if not TOKEN:
    raise ValueError("TOKEN не найден")

ADMIN_CHAT_ID = 712908007
PHOTOS_DIR = "photos"
PHRASES_FILE = "phrases.txt"
DB_NAME = "stats.db"

# ─── LOAD PHOTOS ───────────────────────────────────
all_photos = [f for f in os.listdir(PHOTOS_DIR) if f.endswith(".jpg")]
if not all_photos:
    raise ValueError("Нет jpg в папке photos")
photo_queue = []

def get_next_photo():
    global photo_queue
    if not photo_queue:
        photo_queue = all_photos.copy()
        random.shuffle(photo_queue)
    return photo_queue.pop()

# ─── LOAD PHRASES ──────────────────────────────────
if not os.path.exists(PHRASES_FILE):
    raise ValueError(f"{PHRASES_FILE} не найден")
with open(PHRASES_FILE, encoding="utf-8") as f:
    PHRASES = [line.strip() for line in f if line.strip()]
if not PHRASES:
    raise ValueError("phrases.txt пустой")

# ─── KEYBOARD ──────────────────────────────────────
keyboard = [
    ["Мотивирующая фраза 🌸", "Милая фотка 🐶"],
    ["Я желаю… 💭"]
]
reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,
    one_time_keyboard=False
)

# ─── DATABASE ─────────────────────────────────────
def db_conn():
    return sqlite3.connect(DB_NAME)

def log_action(user, action):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            timestamp TEXT
        )
    """)
    now = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO users (user_id, username, first_name, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_seen=?, username=?, first_name=?
    """, (user.id, user.username, user.first_name, now, now, now, user.username, user.first_name))
    cur.execute("INSERT INTO actions (user_id, action, timestamp) VALUES (?, ?, ?)", (user.id, action, now))
    conn.commit()
    conn.close()

def save_wish(user, wish_text):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            wish TEXT,
            timestamp TEXT
        )
    """)
    cur.execute("INSERT INTO wishes (user_id, wish, timestamp) VALUES (?, ?, ?)",
                (user.id, wish_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_wishes():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, wish, timestamp FROM wishes ORDER BY timestamp ASC")
    rows = cur.fetchall()
    conn.close()
    return rows

# ─── NOTIFY ADMIN ──────────────────────────────────
async def notify_admin(context, user, action):
    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"👤 {user.first_name} (@{user.username or 'нет'}, id={user.id}) → {action}"
    )

# ─── ACTIONS ──────────────────────────────────────
async def send_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(PHRASES), reply_markup=reply_markup)

async def send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = get_next_photo()
    await update.message.reply_photo(
        photo=open(os.path.join(PHOTOS_DIR, photo), "rb"),
        reply_markup=reply_markup
    )

async def start_wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_for_wish"] = True
    await update.message.reply_text(
        "💭 Напиши, пожалуйста, чего ты хочешь.\nЯ обязательно это запомню 💛",
        reply_markup=reply_markup
    )

# ─── BUTTONS MAP ──────────────────────────────────
BUTTONS = {
    "Мотивирующая фраза 🌸": send_phrase,
    "Милая фотка 🐶": send_photo,
    "Я желаю… 💭": start_wish
}

# ─── BOT LOGIC ───────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_action(user, "start")
    await notify_admin(context, user, "start")
    await update.message.reply_text("Привет 💛\nНажимай на кнопки внизу ⬇️", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # Обработка желания
    if context.user_data.get("waiting_for_wish"):
        context.user_data.pop("waiting_for_wish")
        save_wish(user, text)
        log_action(user, "wish_sent")
        await context.bot.send_message(
            ADMIN_CHAT_ID,
            f"💭 Новая хотелка от {user.first_name}:\n«{text}»"
        )
        await update.message.reply_text("Спасибо 💛 Я запомнил твоё желание ✨", reply_markup=reply_markup)
        return

    # Кнопки
    if text in BUTTONS:
        handler = BUTTONS[text]
        log_action(user, text)
        await notify_admin(context, user, text)
        await handler(update, context)
        return

    # Неизвестное
    await update.message.reply_text("Нажимай кнопки внизу ⬇️", reply_markup=reply_markup)

async def wishes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    wishes = get_all_wishes()
    if not wishes:
        await update.message.reply_text("💭 Список желаний пуст")
        return
    lines = ["💭 Список желаний:\n"]
    for i, (_, wish, ts) in enumerate(wishes, 1):
        date = ts.split("T")[0]
        lines.append(f"{i}. {date} — {wish}")
    await update.message.reply_text("\n".join(lines))

# ─── RUN ──────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("wishes", wishes_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    print("Бот запущен")
    app.run_polling()
