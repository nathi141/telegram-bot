import logging
import sqlite3
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================= CONFIG =================
TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"
TON_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"
ADMIN_IDS = [8366726152, 6502235975]
CHANNELS = ["@DigitalAdCentral", "@GlobalAds_Hub"]
GROUP = "@AdMastersCommunity"
POST_INTERVAL = 3600  # seconds

# ================= DATABASE =================
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS referrals (referrer_id INTEGER PRIMARY KEY, count INTEGER DEFAULT 0)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS ads (ad_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text TEXT, link TEXT, amount REAL, status TEXT DEFAULT 'pending')""")
cursor.execute("""CREATE TABLE IF NOT EXISTS withdrawals (withdraw_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, status TEXT DEFAULT 'pending')""")
conn.commit()

# ================= MENU =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Earn Money", callback_data="earn")],
        [InlineKeyboardButton("👥 Referrals", callback_data="ref")],
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📢 Ads", callback_data="ads")],
        [InlineKeyboardButton("🛠 Tools", callback_data="tools")]
    ])

# ================= MESSAGE & BUTTONS HANDLERS =================
# ... keep all your start(), buttons(), messages(), approve(), approve_withdraw() exactly as before ...

# ================= AUTO POST =================
posts = [
    {"text":"📢 Run ads to real users!","image":"https://i.imgur.com/0Z1w3sD.png"},
    {"text":"💰 3 ways to make money online!","image":"https://i.imgur.com/U1Cz4hG.png"},
    {"text":"📊 Best time to run ads!","image":"https://i.imgur.com/5vH4rT7.png"}
]
last_post_index = -1

async def auto_post(context: ContextTypes.DEFAULT_TYPE):
    global last_post_index
    all_chats = CHANNELS + [GROUP]
    available_indices = [i for i in range(len(posts)) if i != last_post_index]
    post_index = random.choice(available_indices)
    last_post_index = post_index
    post = posts[post_index]

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Join Group", url="https://t.me/AdMastersCommunity")],
        [InlineKeyboardButton("🌐 Learn More", url="https://t.me/DigitalAdCentral")]
    ])

    for chat in all_chats:
        try:
            await context.bot.send_photo(chat_id=chat, photo=post["image"], caption=post["text"], reply_markup=buttons, disable_notification=True)
        except Exception as e:
            logging.error(f"Auto post failed for {chat}: {e}")

# ================= RUN BOT CRASH-PROOF =================
async def run_bot_forever():
    while True:
        try:
            app = ApplicationBuilder().token(TOKEN).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CallbackQueryHandler(buttons))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
            app.add_handler(CommandHandler("approve", approve))
            app.add_handler(CommandHandler("approve_withdraw", approve_withdraw))

            # Add auto-post job
            app.job_queue.run_repeating(auto_post, interval=POST_INTERVAL, first=10)

            # This is the **correct way in PTB v20+**:
            await app.run_polling()
        except Exception as e:
            logging.error(f"Bot crashed: {e}. Restarting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_bot_forever())
