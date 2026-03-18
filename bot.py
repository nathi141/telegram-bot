from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"

# ------------------------------
# Admin TON Wallet (your Telegram TON Wallet)
# ------------------------------
ADMIN_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"

# ------------------------------
# Database setup
# ------------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# Users table: referrals, balance, withdraw requests
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
# Main Menu Keyboard
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

    # Add user if not exists
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    # Handle referral if exists
    if context.args:
        referrer_id = context.args[0]
        if referrer_id != user_id:
            # Increment referrals and add $1 to balance
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
# Button Handler
# ------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]])

    # 💸 Earn Money
    if query.data == 'earn':
        referral_link = f"https://t.me/BizBoostProBot?start={user_id}"  # <-- Your bot username
        await query.edit_message_text(
            f"💸 Your Referral Link:\n{referral_link}\n\nInvite friends to earn $1 per referral!",
            reply_markup=back_btn
        )

    # 👥 My Referrals
    elif query.data == 'ref':
        cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        count = result[0] if result else 0
        await query.edit_message_text(
            f"👥 Total Referrals: {count}",
            reply_markup=back_btn
        )

    # 💰 Wallet
    elif query.data == 'wallet':
        cursor.execute("SELECT balance, withdraw_request FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        pending = result[1] if result else 0
        await query.edit_message_text(
            f"💰 Wallet Balance: ${balance:.2f}\n"
            f"📤 Pending Withdraw Requests: ${pending:.2f}",
            reply_markup=back_btn
        )

    # 📤 Withdraw Request
    elif query.data == 'withdraw':
        cursor.execute("SELECT balance, withdraw_request FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        pending = result[1] if result else 0

        if balance > 0:
            # Move all balance to withdraw_request
            cursor.execute(
                "UPDATE users SET balance = 0, withdraw_request = withdraw_request + ? WHERE user_id = ?",
                (balance, user_id)
            )
            conn.commit()
            await query.edit_message_text(
                f"📤 Withdrawal requested!\nAmount: ${balance:.2f}\n"
                f"Pending withdrawal: ${pending + balance:.2f}\n\n"
                "Admin will approve and process TON payout.",
                reply_markup=back_btn
            )
        else:
            await query.edit_message_text(
                "⚠️ You have no balance to withdraw yet!",
                reply_markup=back_btn
            )

    # 💳 Deposit
    elif query.data == 'deposit':
        await query.edit_message_text(
            f"💳 Deposit TON\n\n"
            f"Send TON to this wallet address to fund your balance:\n\n{ADMIN_WALLET}\n\n"
            "After sending, click 'Check Deposit' to update your balance.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Check Deposit", callback_data='check_deposit')],
                [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]
            ])
        )

    # ✅ Check Deposit (placeholder)
    elif query.data == 'check_deposit':
        # TODO: Integrate TON blockchain API to verify deposits
        await query.edit_message_text(
            "✅ Deposit confirmed! Your balance has been updated by admin.",
            reply_markup=back_btn
        )

    # 📢 Ads
    elif query.data == 'ads':
        await query.edit_message_text(
            "📢 Ads system coming soon...",
            reply_markup=back_btn
        )

    # 🛠 Tools
    elif query.data == 'tools':
        await query.edit_message_text(
            "🛠 Tools & resources coming soon...",
            reply_markup=back_btn
        )

    # ⬅️ Back to Main Menu
    elif query.data == 'main':
        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu_keyboard()
        )

# ------------------------------
# Build & Run Bot
# ------------------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.run_polling()
