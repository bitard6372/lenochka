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
DB_NAME = "stats.db"

# ─── PHOTOS ────────────────────────────────────────
all_photos = [f for f in os.listdir(PHOTOS_DIR) if f.endswith(".jpg")]
if not all_photos:
    raise ValueError("Нет jpg в photos")
photo_queue = []

def get_next_photo():
    global photo_queue
    if not photo_queue:
        photo_queue = all_photos.copy()
        random.shuffle(photo_queue)
    return photo_queue.pop()

# ─── PHRASES (оставил только начало, вставь все) ───
PHRASES = [
    "Леночка, ты невероятная, не забывай об этом 🌸",
    "Дыши глубоко, всё наладится, я верю в тебя ❤️",
    "Ты сильная, смелая и замечательная, Леночка 🌈",
    "Не переживай слишком сильно, мир любит тебя 🌼",
    "Каждый день — новая возможность, Леночка ✨",
    "Ты заслуживаешь счастья и тепла, не забывай 🌷",
    "Леночка, помни, что твои чувства важны и их можно отпустить 💛",
    "Ты можешь всё, что задумала, просто поверь в себя 💫",
    "Смейся, даже если сегодня трудно, Леночка 😺",
    "Ты делаешь мир ярче, просто будь собой 🌟",
    "Леночка, всё, что тебя тревожит, пройдёт 🕊️",
    "Не спеши, дыши и делай маленькие шаги 🌸",
    "Ты уже проделала огромную работу, Леночка 👏",
    "Любой шторм заканчивается, и солнце обязательно выйдет ☀️",
    "Леночка, знай: твоя доброта делает этот мир лучше 💖",
    "Ты умеешь справляться с трудностями, даже если сейчас тяжело 🌷",
    "Позволь себе отдохнуть и улыбнуться 😊",
    "Леночка, ты заслуживаешь любви и заботы 🌹",
    "Каждое твое чувство важно, не подавляй его 💛",
    "Ты не одна, мир и я с тобой 🌈",
    "Леночка, сегодня хороший день для маленькой радости 🍀",
    "Ты талантлива, умна и прекрасна 🌟",
    "Не бойся ошибок, они делают тебя сильнее 💫",
    "Леночка, улыбнись, даже маленькая улыбка — это магия 😺",
    "Ты способна на большее, чем думаешь 🌼",
    "Всё будет хорошо, просто доверяй себе 🌷",
    "Леночка, ты удивительная, не сомневайся 🌸",
    "Пусть сегодня будет минутка покоя и тепла 💖",
    "Ты умеешь справляться с любыми бурями, Леночка 🕊️",
    "Помни, что маленькие победы — это тоже успех 🌟",
    "Леночка, позволь себе почувствовать радость сегодня 😊",
    "Ты достойна самых тёплых слов и объятий 💛",
    "Даже в трудные моменты ты остаёшься прекрасной 🌷",
    "Леночка, твоя энергия делает этот мир светлее ✨",
    "Доверяй себе, ты всё сможешь 💫",
    "Ты уже много прошла, гордись собой 🌹",
    "Леночка, иногда отдых — это лучший способ быть сильной 🌼",
    "Ты прекрасна такой, какая есть 😺",
    "Пусть сегодня будет маленькое чудо для тебя 💖",
    "Леночка, твоя улыбка — это солнце для других 🌸",
    "Ты способна на невероятное, поверь 🌈",
    "Даже если тяжело, каждый шаг — это прогресс 🌷",
    "Леночка, будь мягкой к себе, ты заслуживаешь заботы 🕊️",
    "Ты уникальна, помни об этом ✨",
    "Леночка, каждый твой день — это маленькая победа 💛",
    "Ты светишь даже в самые пасмурные дни 🌟",
    "Леночка, ты справишься с этим, я знаю 😺",
    "Пусть любовь к себе станет твоей силой 🌸",
    "Ты прекрасна, даже когда сомневаешься 💖",
    "Леночка, доверяй своим ощущениям и чувствам 🌷",
    "Каждое утро — шанс начать с чистого листа 🌈"
    "Ты самое тёплое, что есть в моём дне 🌞💛",
    "С тобой даже обычные моменты становятся особенными 🌸✨",
    "Мир с тобой ощущается добрее 🌈💖",
    "Ты делаешь мою жизнь светлее ☀️🌷",
    "Улыбка — это твоя суперсила 😺💫",
    "Спасибо, что ты есть 💛🙏",
    "С тобой хочется быть лучше 🌟💖",
    "Ты мой уют 🕊️🌿",
    "Каждый день с тобой это маленькое счастье 🍀😊",
    "Ты вдохновляешь просто тем, что рядом 🌷💫",
    "Мне нравится, что ты есть в этом мире 🌼💛",
    "С тобой всё ощущается правильным 🌟🌸",
    "Ты моя любовь ❤️🌈",
    "Твоя нежность бесценна 💖🕊️",
    "Ты умеешь делать день теплее ☀️🌹",
    "Я благодарен судьбе за тебя 🙏💛",
    "С тобой легко и спокойно 🌿🌸",
    "Ты моя радость 😺✨",
    "Даже котики завидуют твоей милоте 🐱💖",
    "Ты украшаешь этот день 🌸🌞",
    "Мне нравится думать о тебе 💛💫",
    "Ты лучшее, что со мной случалось 🌷❤️",
    "С тобой хочется делиться всем 🌈💖",
    "Ты делаешь мир мягче 🌼🕊️",
    "Ты моё счастье ☀️💛",
    "Спасибо за твою доброту 🌸🙏",
    "С тобой всегда тепло 🌞💖",
    "Ты освящаешь этот день 🌟🌷",
    "Ты делаешь меня счастливым 😺💫",
    "Мне повезло, что ты рядом 🍀❤️",
    "Ты как лучик света ☀️🌈",
    "С тобой даже тишина приятная 🌿✨",
    "Ты моя зайка 🐇💛",
    "Я улыбаюсь, когда думаю о тебе 😺💖",
    "Ты моё вдохновение 🌷💫",
    "Улыбнись! 😊🌸",
    "Мне хорошо, когда ты рядом 🕊️❤️",
    "Ты мой маленький праздник 🎉💛",
    "Ты лучше всех 🌟😺",
    "Не описать словами мою любовь к тебе 💖🌈",
    "Спасибо 🙏🌸",
    "Ты моя нежность 🌷💛",
    "Я знаю, что ты стараешься 💫💖",
    "Ты моя радость каждый день 😺🌼",
    "С тобой хочется улыбаться 😊🌟"
]

# ─── КЛАВИАТУРА ─────────────────────────────────────
keyboard = [
    ["Мотивирующая фраза 🌸", "Милая фотка 🐶"],
    ["Я желаю… 💭"]               # ← убрали "Помощь"
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ─── DATABASE ───────────────────────────────────────
def db_conn():
    return sqlite3.connect(DB_NAME)

def log_action(user, action):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, first_seen TEXT, last_seen TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, timestamp TEXT)")
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
    cur.execute("CREATE TABLE IF NOT EXISTS wishes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, wish TEXT, timestamp TEXT)")
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

# ─── NOTIFY ─────────────────────────────────────────
async def notify_admin(context, user, action):
    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"👤 {user.first_name} (@{user.username or 'нет'}, id={user.id}) → {action}"
    )

# ─── ACTIONS ────────────────────────────────────────
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

# ─── HANDLERS MAP ───────────────────────────────────
BUTTONS = {
    "Мотивирующая фраза 🌸": ("phrase", send_phrase),
    "Милая фотка 🐶":        ("photo",  send_photo),
    "Я желаю… 💭":           ("wish_start", start_wish),
}

# ─── BOT LOGIC ──────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_action(user, "start")
    await notify_admin(context, user, "start")
    await update.message.reply_text("Привет 💛\nНажимай на кнопки внизу ⬇️", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # Обработка желания
    if context.user_data.get("waiting_for_wish"):
        context.user_data.pop("waiting_for_wish")
        save_wish(user, text)
        await log_action(user, "wish_sent")
        await context.bot.send_message(
            ADMIN_CHAT_ID,
            f"💭 Новая хотелка от {user.first_name}:\n«{text}»"
        )
        await update.message.reply_text("Спасибо 💛 Я запомнил твоё желание ✨", reply_markup=reply_markup)
        return

    # Кнопки
    if text in BUTTONS:
        action, handler = BUTTONS[text]
        await log_action(user, action)
        await notify_admin(context, user, action)
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

# ─── RUN ────────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("wishes", wishes_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    print("Бот запущен")
    app.run_polling()
