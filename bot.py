from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import sqlite3
import requests

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"  # Your Bot Token
TON_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"  # Your TON Wallet
TON_API_KEY = "41d6584cbce3d9d50c0ca67e38becfe1154236dfe27a7ff8f0992e2b7c613ace"  # TON API Key
ADMIN_IDS = [8366726152, 6502235975]  # Admin Telegram IDs as integers

# ================= DATABASE =================
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS referrals (referrer_id INTEGER, count INTEGER DEFAULT 0)")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ads (
    ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    link TEXT,
    amount REAL,
    status TEXT DEFAULT 'pending'
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    withdraw_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    status TEXT DEFAULT 'pending'
)
""")
conn.commit()

# ================= MAIN MENU =================
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
        ref = int(context.args[0])
        if ref != user_id:
            cursor.execute("INSERT OR IGNORE INTO referrals(referrer_id,count) VALUES(?,0)", (ref,))
            cursor.execute("UPDATE referrals SET count = count + 1 WHERE referrer_id=?", (ref,))
            conn.commit()

    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\nChoose an option 👇",
        reply_markup=main_menu()
    )

# ================= BUTTON HANDLER =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])

    if q.data == "earn":
        link = f"https://t.me/BizBoostProBot?start={user_id}"
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]
        await q.edit_message_text(f"💸 Balance: {bal} TON\n\nInvite:\n{link}", reply_markup=back)

    elif q.data == "ref":
        cursor.execute("SELECT count FROM referrals WHERE referrer_id=?", (user_id,))
        row = cursor.fetchone()
        count = row[0] if row else 0
        await q.edit_message_text(f"👥 Referrals: {count}", reply_markup=back)

    elif q.data == "wallet":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]
        await q.edit_message_text(f"💰 Balance: {bal} TON\nDeposit to:\n{TON_WALLET}\n\nTo withdraw use Tools → Withdraw", reply_markup=back)

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

# ================= MESSAGE HANDLER =================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # ---------------- Ads Flow ----------------
    step = context.user_data.get("step")
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
        try:
            amount = float(text)
        except:
            await update.message.reply_text("Enter a number")
            return

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]
        if bal < amount:
            await update.message.reply_text("❌ Not enough balance")
            context.user_data.clear()
            return

        cursor.execute("INSERT INTO ads(user_id,text,link,amount) VALUES(?,?,?,?)",
                       (user_id, context.user_data["ad_text"], context.user_data["ad_link"], amount))
        conn.commit()
        ad_id = cursor.lastrowid

        for admin in ADMIN_IDS:
            await context.bot.send_message(
                admin,
                f"📢 New Ad #{ad_id} submitted by {user_id}\n\n{context.user_data['ad_text']}\n{context.user_data['ad_link']}\n💰 Budget: {amount}\n\nApprove: /approve {ad_id}"
            )

        await update.message.reply_text("✅ Ad submitted for approval")
        context.user_data.clear()

    # ---------------- Withdraw Flow ----------------
    if step == "withdraw_amount":
        try:
            amount = float(text)
        except:
            await update.message.reply_text("Enter a valid number")
            return

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]
        if bal < amount:
            await update.message.reply_text("❌ Insufficient balance")
            context.user_data.clear()
            return

        cursor.execute("INSERT INTO withdrawals(user_id,amount) VALUES(?,?)", (user_id, amount))
        conn.commit()

        for admin in ADMIN_IDS:
            await context.bot.send_message(
                admin,
                f"💰 Withdrawal request by {user_id}\nAmount: {amount}\nApprove: /approve_withdraw {cursor.lastrowid}"
            )
        await update.message.reply_text("✅ Withdrawal submitted for admin approval")
        context.user_data.clear()

# ================= ADMIN COMMANDS =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied")
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve <ad_id>")
        return

    ad_id = int(context.args[0])
    cursor.execute("SELECT user_id, amount, status FROM ads WHERE ad_id=? AND status='pending'", (ad_id,))
    ad = cursor.fetchone()
    if not ad:
        await update.message.reply_text("❌ Ad not found or already approved")
        return

    ad_user, amount, _ = ad
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, ad_user))
    cursor.execute("UPDATE ads SET status='approved' WHERE ad_id=?", (ad_id,))
    conn.commit()
    await context.bot.send_message(ad_user, f"✅ Your ad #{ad_id} is approved")
    await update.message.reply_text(f"✅ Ad #{ad_id} approved and balance deducted")

async def approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied")
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve_withdraw <withdraw_id>")
        return
    wid = int(context.args[0])
    cursor.execute("SELECT user_id, amount, status FROM withdrawals WHERE withdraw_id=? AND status='pending'", (wid,))
    req = cursor.fetchone()
    if not req:
        await update.message.reply_text("❌ Request not found")
        return
    w_user, amount, _ = req
    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, w_user))
    cursor.execute("UPDATE withdrawals SET status='approved' WHERE withdraw_id=?", (wid,))
    conn.commit()
    await context.bot.send_message(w_user, f"✅ Your withdrawal of {amount} TON is approved")
    await update.message.reply_text(f"✅ Withdrawal #{wid} approved")

# ================= BOT =================
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("approve_withdraw", approve_withdraw))

app.run_polling()
