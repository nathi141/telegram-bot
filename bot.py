from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8777576356:AAF5WKlcBPE1mszTBs6otvWdvwxgr9dFISs"

# Store users and referrals (simple memory storage)
users = {}
referrals = {}

# Main menu keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Earn Money", callback_data='earn')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command with referral tracking
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check referral
    if context.args:
        referrer_id = context.args[0]
        if referrer_id != str(user_id):
            referrals[referrer_id] = referrals.get(referrer_id, 0) + 1

    users[user_id] = True

    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\n"
        "Earn money by inviting others and using our tools.\n\n"
        "Choose an option below 👇",
        reply_markup=main_menu_keyboard()
    )

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='main')]])

    if query.data == 'earn':
        referral_link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        await query.edit_message_text(
            f"💸 Earn Money!\n\n"
            f"Invite friends using your link:\n{referral_link}\n\n"
            f"Earn rewards for every user that joins!",
            reply_markup=back_btn
        )

    elif query.data == 'ref':
        count = referrals.get(user_id, 0)
        await query.edit_message_text(
            f"👥 Your Referrals: {count}\n\n"
            f"Keep inviting more people to earn more!",
            reply_markup=back_btn
        )

    elif query.data == 'wallet':
        await query.edit_message_text(
            "💰 Wallet system coming soon!",
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
