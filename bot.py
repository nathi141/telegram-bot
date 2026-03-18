from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"
ADMIN_IDS = ["6502235975", "8366726152"]
ADS_CHANNEL = "@your_channel_username"
ADMIN_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrals INTEGER DEFAULT 0
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
def main_menu():
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

    # Referral system
    if context.args:
        ref = context.args[0]
        if ref != user_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1, balance = balance + 1 WHERE user_id=?", (ref,))
            conn.commit()

    await update.message.reply_text(
        "🚀 Welcome to BizBoostPro\n\nChoose an option below:",
        reply_markup=main_menu()
    )

# ---------------- BUTTON HANDLER ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = str(q.from_user.id)

    back = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data='main')]
    ])

    if q.data == "earn":
        link = f"https://t.me/BizBoostProBot?start={user_id}"
        await q.edit_message_text(
            f"💸 Your referral link:\n{link}\n\nEarn $1 per referral!",
            reply_markup=back
        )

    elif q.data == "ref":
        cursor.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
        ref = cursor.fetchone()[0]
        await q.edit_message_text(f"👥 Total Referrals: {ref}", reply_markup=back)

    elif q.data == "wallet":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]
        await q.edit_message_text(
            f"💰 Balance: ${bal}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Deposit", callback_data='deposit')],
                [InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')],
                [InlineKeyboardButton("⬅️ Back", callback_data='main')]
            ])
        )

    elif q.data == "deposit":
        await q.edit_message_text(
            f"💳 Send TON to this address:\n{ADMIN_WALLET}\n\nAfter payment, contact admin.",
            reply_markup=back
        )

    elif q.data == "withdraw":
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]

        if bal <= 0:
            await q.edit_message_text("❌ No balance to withdraw", reply_markup=back)
        else:
            for admin in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin,
                    text=f"💸 Withdraw Request\nUser: {user_id}\nAmount: ${bal}"
                )

            cursor.execute("UPDATE users SET balance=0 WHERE user_id=?", (user_id,))
            conn.commit()

            await q.edit_message_text("✅ Withdraw request sent", reply_markup=back)

    elif q.data == "ads":
        context.user_data["step"] = "text"
        await q.edit_message_text("📢 Send your Ad TEXT")

    elif q.data == "tools":
        await q.edit_message_text(
            "🛠 Tools:\n\n💼 Business ideas\n📊 Growth tips\n💰 Passive income",
            reply_markup=back
        )

    elif q.data == "main":
        await q.edit_message_text("🏠 Main Menu", reply_markup=main_menu())

# ---------------- USER MESSAGE HANDLER ----------------
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if "step" in context.user_data:

        if context.user_data["step"] == "text":
            context.user_data["ad_text"] = text
            context.user_data["step"] = "link"
            await update.message.reply_text("🔗 Send your Ad LINK")

        elif context.user_data["step"] == "link":
            context.user_data["ad_link"] = text
            context.user_data["step"] = "budget"
            await update.message.reply_text("💰 Enter your budget")

        elif context.user_data["step"] == "budget":
            try:
                budget = float(text)

                cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
                bal = cursor.fetchone()[0]

                if bal < budget:
                    await update.message.reply_text(
                        f"❌ Not enough balance\nBalance: ${bal}\nNeeded: ${budget}"
                    )
                    context.user_data.clear()
                    return

                cursor.execute(
                    "INSERT INTO ads (user_id, text, link, budget, status) VALUES (?, ?, ?, ?, ?)",
                    (user_id, context.user_data["ad_text"], context.user_data["ad_link"], budget, "pending")
                )
                conn.commit()

                ad_id = cursor.lastrowid

                for admin in ADMIN_IDS:
                    await context.bot.send_message(
                        chat_id=admin,
                        text=(
                            f"🚨 NEW AD\n\nUser: {user_id}\nAd ID: {ad_id}\n\n"
                            f"{context.user_data['ad_text']}\n\n"
                            f"{context.user_data['ad_link']}\n\nBudget: ${budget}"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{ad_id}")],
                            [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{ad_id}")]
                        ])
                    )

                context.user_data.clear()
                await update.message.reply_text("✅ Ad sent for approval")

            except:
                await update.message.reply_text("❌ Invalid amount")

# ---------------- ADMIN APPROVAL ----------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    admin_id = str(q.from_user.id)

    if admin_id not in ADMIN_IDS:
        return

    if q.data.startswith("approve_"):
        ad_id = q.data.split("_")[1]

        cursor.execute("SELECT text, link, user_id, budget FROM ads WHERE id=?", (ad_id,))
        ad = cursor.fetchone()

        if not ad:
            await q.edit_message_text("❌ Not found")
            return

        text, link, user_id, budget = ad

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = cursor.fetchone()[0]

        if bal < budget:
            await q.edit_message_text("❌ User has no balance")
            return

        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (budget, user_id))
        conn.commit()

        await context.bot.send_message(
            chat_id=ADS_CHANNEL,
            text=f"{text}\n\n👉 {link}"
        )

        cursor.execute("UPDATE ads SET status='approved' WHERE id=?", (ad_id,))
        conn.commit()

        await q.edit_message_text("✅ Approved & Posted")

    elif q.data.startswith("reject_"):
        ad_id = q.data.split("_")[1]

        cursor.execute("UPDATE ads SET status='rejected' WHERE id=?", (ad_id,))
        conn.commit()

        await q.edit_message_text("❌ Rejected")

# ---------------- RUN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(CallbackQueryHandler(admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

app.run_polling()
