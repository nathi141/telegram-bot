from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"

ADMIN_IDS = ["6502235975", "8366726152"]
ADS_CHANNEL = "@YourAdsChannelUsername"
ADMIN_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    withdraw REAL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    text TEXT,
    link TEXT,
    budget REAL,
    status TEXT
)
""")

conn.commit()

# ---------------- MENU ----------------
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Earn", callback_data='earn')],
        [InlineKeyboardButton("👥 Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📢 Ads", callback_data='ads')],
        [InlineKeyboardButton("🛠 Tools", callback_data='tools')]
    ])

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    # referral
    if context.args:
        ref = context.args[0]
        if ref != user_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1, balance = balance + 1 WHERE user_id = ?", (ref,))
            conn.commit()

    await update.message.reply_text(
        "🚀 Welcome to BizBoostPro\n\nChoose an option below:",
        reply_markup=menu()
    )

# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = str(q.from_user.id)

    back = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='main')]])

    if q.data == "earn":
        link = f"https://t.me/BizBoostProBot?start={user_id}"
        await q.edit_message_text(f"💸 Your referral link:\n{link}", reply_markup=back)

    elif q.data == "ref":
        cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
        r = cursor.fetchone()[0]
        await q.edit_message_text(f"👥 Referrals: {r}", reply_markup=back)

    elif q.data == "wallet":
        cursor.execute("SELECT balance, withdraw FROM users WHERE user_id=?", (user_id,))
        b, w = cursor.fetchone()
        await q.edit_message_text(
            f"💰 Balance: ${b}\nPending Withdraw: ${w}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')],
                [InlineKeyboardButton("💳 Deposit", callback_data='deposit')],
                [InlineKeyboardButton("⬅️ Back", callback_data='main')]
            ])
        )

    elif q.data == "deposit":
        await q.edit_message_text(
            f"💳 Send TON to:\n{ADMIN_WALLET}\n\nThen send /confirm",
            reply_markup=back
        )

    elif q.data == "withdraw":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        b = cursor.fetchone()[0]
        if b > 0:
            cursor.execute("UPDATE users SET balance=0, withdraw=withdraw+? WHERE user_id=?", (b, user_id))
            conn.commit()
            await q.edit_message_text("✅ Withdraw request sent", reply_markup=back)
        else:
            await q.edit_message_text("❌ No balance", reply_markup=back)

    elif q.data == "ads":
        context.user_data["ad_step"] = "text"
        await q.edit_message_text("📢 Send your Ad TEXT")

    elif q.data == "tools":
        await q.edit_message_text(
            "🛠 Tools:\n\n"
            "💼 Business ideas\n"
            "📊 Growth tips\n"
            "💰 Passive income\n"
            "📢 Promotion services",
            reply_markup=back
        )

    elif q.data == "main":
        await q.edit_message_text("🏠 Main Menu", reply_markup=menu())


    async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    # Ads flow
    if "ad_step" in context.user_data:

        if context.user_data["ad_step"] == "text":
            context.user_data["ad_text"] = text
            context.user_data["ad_step"] = "link"
            await update.message.reply_text("🔗 Send your Ad LINK")

        elif context.user_data["ad_step"] == "link":
            context.user_data["ad_link"] = text
            context.user_data["ad_step"] = "budget"
            await update.message.reply_text("💰 Enter budget amount")

        elif context.user_data["ad_step"] == "budget":
            try:
                budget = float(text)

                cursor.execute(
                    "INSERT INTO ads (user_id, text, link, budget, status) VALUES (?, ?, ?, ?, ?)",
                    (user_id, context.user_data["ad_text"], context.user_data["ad_link"], budget, "pending")
                )
                conn.commit()

                # Get last inserted ad ID
                ad_id = cursor.lastrowid

                # Send to ALL admins instantly
                for admin in ADMIN_IDS:
                    await context.bot.send_message(
                        chat_id=admin,
                        text=(
                            f"🚨 New Ad Submission\n\n"
                            f"User: {user_id}\n"
                            f"Ad ID: {ad_id}\n\n"
                            f"{context.user_data['ad_text']}\n\n"
                            f"🔗 {context.user_data['ad_link']}\n"
                            f"💰 Budget: ${budget}"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{ad_id}")],
                            [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{ad_id}")]
                        ])
                    )

                context.user_data.clear()

                await update.message.reply_text("✅ Ad submitted successfully and sent to admin")

            except:
                await update.message.reply_text("❌ Invalid budget")

    # Ads flow
    if "ad_step" in context.user_data:

        if context.user_data["ad_step"] == "text":
            context.user_data["ad_text"] = text
            context.user_data["ad_step"] = "link"
            await update.message.reply_text("🔗 Send your Ad LINK")

        elif context.user_data["ad_step"] == "link":
            context.user_data["ad_link"] = text
            context.user_data["ad_step"] = "budget"
            await update.message.reply_text("💰 Enter budget amount")

        elif context.user_data["ad_step"] == "budget":
            try:
                budget = float(text)

                cursor.execute(
                    "INSERT INTO ads (user_id, text, link, budget, status) VALUES (?, ?, ?, ?, ?)",
                    (user_id, context.user_data["ad_text"], context.user_data["ad_link"], budget, "pending")
                )
                conn.commit()

                context.user_data.clear()

                await update.message.reply_text("✅ Ad submitted for approval")

            except:
                await update.message.reply_text("❌ Invalid budget")

# ---------------- ADMIN ----------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return

    cursor.execute("SELECT * FROM ads WHERE status='pending'")
    ads = cursor.fetchall()

    for ad in ads:
        ad_id, uid, text, link, budget, status = ad

        await update.message.reply_text(
            f"Ad ID: {ad_id}\nUser: {uid}\n{text}\n{link}\nBudget: ${budget}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{ad_id}")],
                [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{ad_id}")]
            ])
        )

# ---------------- ADMIN BUTTON ----------------
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = str(q.from_user.id)

    if user_id not in ADMIN_IDS:
        return

    if q.data.startswith("approve_"):
        ad_id = q.data.split("_")[1]

        cursor.execute("SELECT text, link FROM ads WHERE id=?", (ad_id,))
        text, link = cursor.fetchone()

        # Post to channel
        await context.bot.send_message(
            chat_id=ADS_CHANNEL,
            text=f"{text}\n\n👉 {link}"
        )

        cursor.execute("UPDATE ads SET status='approved' WHERE id=?", (ad_id,))
        conn.commit()

        await q.edit_message_text("✅ Ad posted")

    elif q.data.startswith("reject_"):
        ad_id = q.data.split("_")[1]
        cursor.execute("UPDATE ads SET status='rejected' WHERE id=?", (ad_id,))
        conn.commit()
        await q.edit_message_text("❌ Ad rejected")

# ---------------- RUN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(CallbackQueryHandler(admin_buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

app.run_polling()
