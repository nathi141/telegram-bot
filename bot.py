from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import sqlite3

# ===== CONFIG =====
TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"
TON_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"
TON_API_KEY = "41d6584cbce3d9d50c0ca67e38becfe1154236dfe27a7ff8f0992e2b7c613ace"
ADMIN_IDS = ["8366726152", "6502235975"]

# ===== DATABASE =====
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, balance REAL DEFAULT 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS referrals (referrer_id TEXT, count INTEGER DEFAULT 0)")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ads (
    ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    text TEXT,
    link TEXT,
    amount REAL,
    status TEXT DEFAULT 'pending'
)
""")
conn.commit()

# ===== MENU =====
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Earn Money", callback_data="earn")],
        [InlineKeyboardButton("👥 Referrals", callback_data="ref")],
        [InlineKeyboardButton("💰 Wallet", callback_data="wallet")],
        [InlineKeyboardButton("📢 Ads", callback_data="ads")]
    ])

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

    if context.args:
        ref = context.args[0]
        if ref != user_id:
            cursor.execute("INSERT OR IGNORE INTO referrals(referrer_id,count) VALUES(?,0)", (ref,))
            cursor.execute("UPDATE referrals SET count = count + 1 WHERE referrer_id=?", (ref,))
            conn.commit()

    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\nChoose an option 👇",
        reply_markup=main_menu()
    )

# ===== BUTTONS =====
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = str(q.from_user.id)

    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]])

    if q.data == "earn":
        link = f"https://t.me/BizBoostProBot?start={user_id}"
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]

        await q.edit_message_text(
            f"💸 Balance: {bal} TON\n\nInvite:\n{link}",
            reply_markup=back
        )

    elif q.data == "ref":
        cursor.execute("SELECT count FROM referrals WHERE referrer_id=?", (user_id,))
        row = cursor.fetchone()
        count = row[0] if row else 0

        await q.edit_message_text(f"👥 Referrals: {count}", reply_markup=back)

    elif q.data == "wallet":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]

        await q.edit_message_text(
            f"💰 Balance: {bal} TON\n\nDeposit to:\n{TON_WALLET}",
            reply_markup=back
        )

    elif q.data == "ads":
        context.user_data["step"] = "text"
        await q.message.reply_text("📢 Send your Ad TEXT")

    elif q.data == "main":
        await q.edit_message_text("🏠 Main Menu", reply_markup=main_menu())

# ===== MESSAGE FLOW =====
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if context.user_data.get("step") == "text":
        context.user_data["ad_text"] = text
        context.user_data["step"] = "link"
        await update.message.reply_text("🔗 Send your Ad LINK")
        return

    if context.user_data.get("step") == "link":
        context.user_data["ad_link"] = text
        context.user_data["step"] = "amount"
        await update.message.reply_text("💰 Enter budget")
        return

    if context.user_data.get("step") == "amount":
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
                f"📢 Ad #{ad_id}\n\n{context.user_data['ad_text']}\n{context.user_data['ad_link']}\n💰 {amount}\n\nApprove: /approve {ad_id}"
            )

        await update.message.reply_text("✅ Sent for approval")
        context.user_data.clear()

# ===== ADMIN APPROVE =====
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Not admin")
        return

    if not context.args:
        await update.message.reply_text("Use: /approve ID")
        return

    ad_id = context.args[0]

    cursor.execute("SELECT user_id,amount FROM ads WHERE ad_id=? AND status='pending'", (ad_id,))
    ad = cursor.fetchone()

    if not ad:
        await update.message.reply_text("❌ Not found")
        return

    ad_user, amount = ad

    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, ad_user))
    cursor.execute("UPDATE ads SET status='approved' WHERE ad_id=?", (ad_id,))
    conn.commit()

    await context.bot.send_message(ad_user, "✅ Your ad is approved")
    await update.message.reply_text(f"✅ Approved #{ad_id}")

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
app.add_handler(CommandHandler("approve", approve))

app.run_polling()
