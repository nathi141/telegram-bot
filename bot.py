import os
import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# ================= LOGGING =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ================= CONFIG =================
TOKEN = os.environ.get("BOT_TOKEN")  # <-- Set BOT_TOKEN in Railway environment variables
TON_WALLET = os.environ.get("TON_WALLET", "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf")
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

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != user_id:
                cursor.execute("INSERT OR IGNORE INTO referrals(referrer_id,count) VALUES(?,0)", (ref,))
                cursor.execute("UPDATE referrals SET count = count + 1 WHERE referrer_id=?", (ref,))
                conn.commit()
        except:
            pass
    await update.message.reply_text("🎉 Welcome to BizBoostPro!\n\nChoose an option 👇", reply_markup=main_menu())

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])
    try:
        if q.data == "earn":
            cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            bal = cursor.fetchone()[0] if cursor.fetchone() else 0
            link = f"https://t.me/BizBoostProBot?start={user_id}"
            await q.edit_message_text(f"💸 Balance: {bal} TON\n\nInvite friends:\n{link}", reply_markup=back)
        elif q.data == "ref":
            cursor.execute("SELECT count FROM referrals WHERE referrer_id=?", (user_id,))
            count = cursor.fetchone()[0] if cursor.fetchone() else 0
            await q.edit_message_text(f"👥 Referrals: {count}", reply_markup=back)
        elif q.data == "wallet":
            cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            bal = cursor.fetchone()[0] if cursor.fetchone() else 0
            await q.edit_message_text(f"💰 Balance: {bal} TON\nDeposit to:\n{TON_WALLET}\n\nWithdraw: Tools → Withdraw", reply_markup=back)
        elif q.data == "ads":
            context.user_data["step"] = "text"
            await q.message.reply_text("📢 Send your Ad TEXT")
        elif q.data == "tools":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("🔗 Referral Link", callback_data="ref")],
                [InlineKeyboardButton("💰 Check Balance", callback_data="wallet")]
            ])
            await q.edit_message_text("🛠 Tools Menu:", reply_markup=keyboard)
        elif q.data == "withdraw":
            context.user_data["step"] = "withdraw_amount"
            await q.message.reply_text("💰 Enter amount to withdraw:")
        elif q.data == "main":
            await q.edit_message_text("🏠 Main Menu", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Buttons error: {e}")

# ================= MESSAGE HANDLER =================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    step = context.user_data.get("step")
    try:
        # ---------- ADS ----------
        if step == "text":
            context.user_data["ad_text"] = text
            context.user_data["step"] = "link"
            await update.message.reply_text("🔗 Send your Ad LINK")
            return
        if step == "link":
            context.user_data["ad_link"] = text
            context.user_data["step"] = "amount"
            await update.message.reply_text("💰 Enter budget")
            return
        if step == "amount":
            amount = float(text)
            cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            bal = cursor.fetchone()[0] if cursor.fetchone() else 0
            if bal < amount:
                await update.message.reply_text("❌ Not enough balance")
                context.user_data.clear()
                return
            cursor.execute("INSERT INTO ads(user_id,text,link,amount) VALUES(?,?,?,?)",
                           (user_id, context.user_data["ad_text"], context.user_data["ad_link"], amount))
            conn.commit()
            ad_id = cursor.lastrowid
            for admin in ADMIN_IDS:
                await context.bot.send_message(admin,
                    f"📢 New Ad #{ad_id} submitted by {user_id}\n{context.user_data['ad_text']}\n{context.user_data['ad_link']}\n💰 Budget: {amount}\nApprove: /approve {ad_id}")
            await update.message.reply_text("✅ Ad submitted for approval")
            context.user_data.clear()
        # ---------- WITHDRAW ----------
        if step == "withdraw_amount":
            amount = float(text)
            cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            bal = cursor.fetchone()[0] if cursor.fetchone() else 0
            if bal < amount:
                await update.message.reply_text("❌ Insufficient balance")
                context.user_data.clear()
                return
            cursor.execute("INSERT INTO withdrawals(user_id,amount) VALUES(?,?)", (user_id, amount))
            conn.commit()
            for admin in ADMIN_IDS:
                await context.bot.send_message(admin,
                    f"💰 Withdrawal request by {user_id}\nAmount: {amount}\nApprove: /approve_withdraw {cursor.lastrowid}")
            await update.message.reply_text("✅ Withdrawal submitted for admin approval")
            context.user_data.clear()
    except Exception as e:
        logging.error(f"Messages error: {e}")

# ================= ADMIN =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: 
        return await update.message.reply_text("❌ Access denied")
    if not context.args: 
        return await update.message.reply_text("Usage: /approve <ad_id>")
    ad_id = int(context.args[0])
    cursor.execute("SELECT user_id, amount, status FROM ads WHERE ad_id=? AND status='pending'", (ad_id,))
    ad = cursor.fetchone()
    if not ad: return await update.message.reply_text("❌ Ad not found or approved")
    ad_user, amount, _ = ad
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, ad_user))
    cursor.execute("UPDATE ads SET status='approved' WHERE ad_id=?", (ad_id,))
    conn.commit()
    await context.bot.send_message(ad_user, f"✅ Your ad #{ad_id} is approved")
    await update.message.reply_text(f"✅ Ad #{ad_id} approved")

async def approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: 
        return await update.message.reply_text("❌ Access denied")
    if not context.args: 
        return await update.message.reply_text("Usage: /approve_withdraw <withdraw_id>")
    wid = int(context.args[0])
    cursor.execute("SELECT user_id, amount, status FROM withdrawals WHERE withdraw_id=? AND status='pending'", (wid,))
    req = cursor.fetchone()
    if not req: return await update.message.reply_text("❌ Request not found")
    w_user, amount, _ = req
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, w_user))
    cursor.execute("UPDATE withdrawals SET status='approved' WHERE withdraw_id=?", (wid,))
    conn.commit()
    await context.bot.send_message(w_user, f"✅ Your withdrawal of {amount} TON is approved")
    await update.message.reply_text(f"✅ Withdrawal #{wid} approved")

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
        [InlineKeyboardButton("👥 Join Group", url=f"https://t.me/AdMastersCommunity")],
        [InlineKeyboardButton("🌐 Learn More", url=f"https://t.me/DigitalAdCentral")]
    ])

    for chat in all_chats:
        try:
            await context.bot.send_photo(chat_id=chat, photo=post["image"], caption=post["text"], reply_markup=buttons, disable_notification=True)
        except Exception as e:
            logging.error(f"Auto post failed for {chat}: {e}")

# ================= RUN BOT =================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("approve_withdraw", approve_withdraw))

    # Schedule auto posting
    app.job_queue.run_repeating(auto_post, interval=POST_INTERVAL, first=10)

    # Run polling forever
    while True:
        try:
            await app.run_polling()
        except Exception as e:
            logging.error(f"Polling error: {e}")

import asyncio
asyncio.run(main())
