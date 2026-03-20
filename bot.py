import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ========== CONFIG ==========
TOKEN = "YOUR_BOT_TOKEN"
TON_WALLET = "YOUR_WALLET_ADDRESS"
ADMIN_IDS = [12345, 67890]
CHANNELS = ["@DigitalAdCentral", "@GlobalAds_Hub"]
GROUP = "@AdMastersCommunity"
POST_INTERVAL = 3600  # seconds

# ========== LOGGING ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== DATABASE ==========
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS referrals (referrer_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS ads (ad_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text TEXT, link TEXT, amount REAL, status TEXT DEFAULT 'pending')")
cursor.execute("CREATE TABLE IF NOT EXISTS withdrawals (withdraw_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, status TEXT DEFAULT 'pending')")
conn.commit()

# ========== MENU ==========
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Earn Money", callback_data="earn")],
        [InlineKeyboardButton("👥 Referrals", callback_data="ref")],
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📢 Ads", callback_data="ads")],
        [InlineKeyboardButton("🛠 Tools", callback_data="tools")]
    ])

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()
    await update.message.reply_text("🎉 Welcome to BizBoostPro!\nChoose an option 👇", reply_markup=main_menu())

# ========== BUTTONS ==========
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])

    try:
        if q.data == "earn":
            cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            bal = row[0] if row else 0
            link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
            await q.edit_message_text(f"💸 Balance: {bal} TON\nInvite: {link}", reply_markup=back)
        elif q.data == "wallet":
            cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            bal = row[0] if row else 0
            await q.edit_message_text(f"💰 Balance: {bal} TON\nDeposit: {TON_WALLET}", reply_markup=back)
        elif q.data == "main":
            await q.edit_message_text("🏠 Main Menu", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Buttons error: {e}")

# ========== MESSAGES ==========
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Message received!")

# ========== AUTO POST ==========
async def auto_post(context: ContextTypes.DEFAULT_TYPE):
    posts = [
        {"text": "📢 Run ads to real users!", "image": "https://i.imgur.com/0Z1w3sD.png"},
        {"text": "💰 3 ways to make money online!", "image": "https://i.imgur.com/U1Cz4hG.png"},
        {"text": "📊 Best time to run ads!", "image": "https://i.imgur.com/5vH4rT7.png"}
    ]
    post = random.choice(posts)
    buttons_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Join Group", url=f"https://t.me/{GROUP[1:]}")],
        [InlineKeyboardButton("🌐 Learn More", url=f"https://t.me/{CHANNELS[0][1:]}")]
    ])
    for chat in CHANNELS + [GROUP]:
        try:
            await context.bot.send_photo(chat_id=chat, photo=post["image"], caption=post["text"], reply_markup=buttons_markup)
        except Exception as e:
            logging.error(f"Auto post failed for {chat}: {e}")

# ========== RUN BOT ==========
def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.job_queue.run_repeating(auto_post, interval=POST_INTERVAL, first=10)
    app.run_polling()

if __name__ == "__main__":
    run_bot()
