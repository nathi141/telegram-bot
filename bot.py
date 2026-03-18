from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"

# Database setup
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

# Main menu
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Earn Money", callback_data='earn')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Add user if not exists
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

    # Handle referral
    if context.args:
        referrer_id = context.args[0]
        if referrer_id != user_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()

    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\nEarn money by inviting others 👇",
        reply_markup=main_menu_keyboard()
    )

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    back_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data='main')]
    ])

    if query.data == 'earn':
        referral_link = f"https://t.me/BizBoostProBot?start={user_id}"
        await query.edit_message_text(
            f"💸 Your Referral Link:\n{referral_link}\n\nInvite and earn!",
            reply_markup=back_btn
        )

    elif query.data == 'ref':
        cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        count = result[0] if result else 0

        await query.edit_message_text(
            f"👥 Total Referrals: {count}",
            reply_markup=back_btn
        )

    elif query.data == 'wallet':
        await query.edit_message_text(
            "💰 Wallet system coming soon...",
            reply_markup=back_btn
        )

    elif query.data == 'main':
        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu_keyboard()
        )

# Run bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
