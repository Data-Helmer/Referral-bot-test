import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")  # DO NOT hardcode token
BOT_USERNAME = "Ekpo_bot"  # without @
POINTS_PER_REFERRAL = 10

# ================= DATABASE =================
conn = sqlite3.connect("referral_campaign.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    referrer_id INTEGER,
    points INTEGER DEFAULT 0
)
""")
conn.commit()

# ================= HELPERS =================
def get_rank(points: int) -> str:
    if points >= 100:
        return "🥇 Gold"
    elif points >= 50:
        return "🥈 Silver"
    elif points >= 20:
        return "🥉 Bronze"
    return "🔰 Beginner"

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username

    referrer_id = None
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except:
            pass

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        await update.message.reply_text("✅ You are already registered.")
        return

    if referrer_id == user_id:
        referrer_id = None

    cursor.execute(
        "INSERT INTO users (user_id, username, referrer_id, points) VALUES (?, ?, ?, 0)",
        (user_id, username, referrer_id)
    )

    if referrer_id:
        cursor.execute(
            "UPDATE users SET points = points + ? WHERE user_id = ?",
            (POINTS_PER_REFERRAL, referrer_id)
        )

    conn.commit()

    await update.message.reply_text(
        "🎉 Welcome to the Referral Campaign!\n\n"
        "Use /referral to get your referral link.\n"
        "Use /rank to check your points."
    )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    await update.message.reply_text(
        f"🔗 Your referral link:\n{link}\n\n"
        f"Earn {POINTS_PER_REFERRAL} points per referral!"
    )

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("❌ You are not registered. Use /start")
        return

    points = row[0]
    await update.message.reply_text(
        f"⭐ Points: {points}\n🏆 Rank: {get_rank(points)}"
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute(
        "SELECT username, points FROM users ORDER BY points DESC LIMIT 10"
    )
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No users yet.")
        return

    text = "🏆 Leaderboard 🏆\n\n"
    for i, (username, points) in enumerate(rows, start=1):
        name = f"@{username}" if username else "Anonymous"
        text += f"{i}. {name} — {points} pts\n"

    await update.message.reply_text(text)

# ================= BOT START =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    print("Referral bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
