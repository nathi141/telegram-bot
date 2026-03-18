from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"

# Admin accounts
ADMIN_IDS = ["6502235975", "8366726152"]  # Both your admin accounts

# TON wallet address
ADMIN_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"

# ------------------------------
# Database
# ------------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    referrals INTEGER DEFAULT 0,
    balance REAL DEFAULT 0,
    withdraw_request REAL DEFAULT 0
)
""")
conn.commit()

# ------------------------------
# Main Menu
# ------------------------------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Earn Money", callback_data='earn')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("💳 Deposit", callback_data='deposit')],
        [InlineKeyboardButton("📢 Ads", callback_data='ads')],
        [InlineKeyboardButton("🛠 Tools", callback_data='tools')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------------------
# /start Command
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    if context.args:
        referrer_id = context.args[0]
        if referrer_id != user_id:
            cursor.execute(
                "UPDATE users SET referrals = referrals + 1, balance = balance + 1 WHERE user_id = ?",
                (referrer_id,)
            )
            conn.commit()

    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\n"
        "Earn money, manage your wallet, deposit TON, and run ads easily.\n\n"
        "Choose an option below 👇",
        reply_markup=main_menu_keyboard()
    )

# ------------------------------
# /admin Command
# ------------------------------
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized.")
        return

    cursor.execute("SELECT user_id, referrals, balance, withdraw_request FROM users")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("No users yet.")
        return

    text = "👨‍💻 Admin Dashboard\n\n"
    for r in rows:
        uid, ref, bal, wreq = r
        text += f"User: {uid}\nReferrals: {ref}\nBalance: ${bal:.2f}\nPending Withdrawal: ${wreq:.2f}\n\n"

    buttons = []
    for r in rows:
        uid, ref, bal, wreq = r
        if wreq > 0:
            buttons.append([InlineKeyboardButton(f"✅ Approve ${wreq:.2f} for {uid}", callback_data=f"approve_{uid}")])

    if buttons:
        buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
    )

# ------------------------------
# Button Handler
# ------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]])

    # Admin Approve Withdraw
    if query.data.startswith("approve_"):
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("❌ Not authorized!")
            return
        target_id = query.data.split("_")[1]
        cursor.execute("UPDATE users SET withdraw_request = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
        await query.edit_message_text(f"✅ Withdrawal approved for user {target_id}.")
        return

    elif query.data == "admin_refresh":
        await admin_dashboard(update, context)
        return

    # Regular Bot Buttons
    if query.data == 'earn':
        referral_link = f"https://t.me/BizBoostProBot?start={user_id}"
        await query.edit_message_text(f"💸 Your Referral Link:\n{referral_link}", reply_markup=back_btn)

    elif query.data == 'ref':
        cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        count = result[0] if result else 0
        await query.edit_message_text(f"👥 Total Referrals: {count}", reply_markup=back_btn)

    elif query.data == 'wallet':
        cursor.execute("SELECT balance, withdraw_request FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        pending = result[1] if result else 0
        await query.edit_message_text(
            f"💰 Wallet Balance: ${balance:.2f}\nPending Withdrawal: ${pending:.2f}", reply_markup=back_btn
        )

    elif query.data == 'withdraw':
        cursor.execute("SELECT balance, withdraw_request FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        if balance > 0:
            cursor.execute(
                "UPDATE users SET balance = 0, withdraw_request = withdraw_request + ? WHERE user_id = ?",
                (balance, user_id)
            )
            conn.commit()
            await query.edit_message_text(
                f"📤 Withdrawal requested: ${balance:.2f}", reply_markup=back_btn
            )
        else:
            await query.edit_message_text("⚠️ No balance to withdraw.", reply_markup=back_btn)

    elif query.data == 'deposit':
        await query.edit_message_text(
            f"💳 Deposit TON\nSend to:\n{ADMIN_WALLET}\n\nClick 'Check Deposit' after sending.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Check Deposit", callback_data='check_deposit')],
                [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]
            ])
        )

    elif query.data == 'check_deposit':
        await query.edit_message_text("✅ Deposit confirmed by admin.", reply_markup=back_btn)

    elif query.data == 'ads':
        await query.edit_message_text("📢 Ads system coming soon...", reply_markup=back_btn)

    elif query.data == 'tools':
        await query.edit_message_text("🛠 Tools coming soon...", reply_markup=back_btn)

    elif query.data == 'main':
        await query.edit_message_text("🏠 Main Menu", reply_markup=main_menu_keyboard())

# ------------------------------
# Build & Run Bot
# ------------------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_dashboard))
app.add_handler(CallbackQueryHandler(button_handler))
app.run_polling()
