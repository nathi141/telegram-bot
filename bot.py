from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g
"

users = {}
referrals = {}

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Earn Money", callback_data='earn')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📢 Ads", callback_data='ads')],
        [InlineKeyboardButton("🛠 Tools", callback_data='tools')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if context.args:
        referrer_id = context.args[0]
        if referrer_id != user_id:
            referrals[referrer_id] = referrals.get(referrer_id, 0) + 1

    users[user_id] = True

    await update.message.reply_text(
        "🎉 Welcome to BizBoostPro!\n\n"
        "Earn money, manage your wallet, and run ads easily.\n\n"
        "Choose an option below 👇",
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    back_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]
    ])

    if query.data == 'earn':
        referral_link = f"https://t.me/BizBoostProBot?start={user_id}"
        await query.edit_message_text(
            f"💸 Earn Money\n\n"
            f"Invite people using your link:\n{referral_link}\n\n"
            f"You earn rewards for every person that joins!",
            reply_markup=back_btn
        )

    elif query.data == 'ref':
        count = referrals.get(user_id, 0)
        await query.edit_message_text(
            f"👥 Your Referrals: {count}\n\n"
            f"Keep inviting to earn more 💸",
            reply_markup=back_btn
        )

    elif query.data == 'wallet':
        await query.edit_message_text(
            "💰 Wallet feature coming soon...",
            reply_markup=back_btn
        )

    elif query.data == 'ads':
        await query.edit_message_text(
            "📢 Ads system coming soon...",
            reply_markup=back_btn
        )

    elif query.data == 'tools':
        await query.edit_message_text(
            "🛠 Tools & resources coming soon...",
            reply_markup=back_btn
        )

    elif query.data == 'main':
        await query.edit_message_text(
            "🏠 Main Menu",
            reply_markup=main_menu_keyboard()
        )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()
