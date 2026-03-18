from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"

# ------------------------------
# Database setup
# ------------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    referrals INTEGER DEFAULT 0,
    balance REAL DEFAULT 0
)
""")
conn.commit()

# ------------------------------
# Main menu keyboard
# ------------------------------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Earn Money", callback_data='earn')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📢 Ads", callback_data='ads')],
        [InlineKeyboardButton("🛠 Tools", callback_data='tools')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------------------
# /start command
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
            # Increment referral count and add $1 to balance
            cursor.execute("UPDATE users SET referrals = referrals + 1, balance = balance + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()

    # Send welcome message
    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\n"
        "Earn money, manage your wallet, and run ads easily.\n\n"
        "Choose an option below 👇",
        reply_markup=main_menu_keyboard()
    )

# ------------------------------
# Button handler
# ------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    back_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]
    ])

    # 💸 Earn Money
    if query.data == 'earn':
        referral_link = f"https://t.me/BizBoostProBot?start={user_id}"  # <-- Replace if your bot username changes
        await query.edit_message_text(
            f"💸 Your Referral Link:\n{referral_link}\n\nInvite and earn $1 per referral!",
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
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        await query.edit_message_text(
            f"💰 Your Wallet Balance: ${balance:.2f}\n\nWithdrawals coming soon!",
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
# Build and run the bot
# ------------------------------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
