from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Your Bot Token
TOKEN = "8777576356:AAF5WKlcBPE1mszTBs6otvWdvwxgr9dFISs"

# Function to create the main menu keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Make money online", callback_data='earn')],
        [InlineKeyboardButton("💰 Manage TON wallet", callback_data='wallet')],
        [InlineKeyboardButton("📢 Create Telegram ads", callback_data='ads')],
        [InlineKeyboardButton("🛠 Tools & Resources", callback_data='tools')],
        [InlineKeyboardButton("📈 Updates & Tips", callback_data='updates')]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "BizBoostProBot 💼🚀\n\n"
        "Your all-in-one digital assistant for growing and managing your online business.\n\n"
        "This bot helps you access and manage your TON wallet, create and run Telegram ads, "
        "and discover smart ways to earn online. It also provides tools, updates, and resources "
        "to help you build and scale your presence across different platforms.\n\n"
        "Whether you’re starting out or looking to grow, BizBoostProBot is here to simplify "
        "everything and boost your success.🚀💸\n\n"
        "Choose an option below to get started 👇"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

# Callback handler for buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge button click

    # “Back to Main Menu” button
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]])

    # Handle each button click
    if query.data == 'earn':
        await query.edit_message_text(
            "💸 Here are ways to earn online using Telegram:\n"
            "1. Share referral links\n"
            "2. Join Telegram affiliate programs\n"
            "3. Sell digital products or services",
            reply_markup=back_button
        )
    elif query.data == 'wallet':
        await query.edit_message_text(
            "💰 Your TON wallet is ready!\n"
            "Check balance, transactions, or manage your wallet here.",
            reply_markup=back_button
        )
    elif query.data == 'ads':
        await query.edit_message_text(
            "📢 Manage your Telegram ads easily!\n"
            "You can create campaigns and track performance here.",
            reply_markup=back_button
        )
    elif query.data == 'tools':
        await query.edit_message_text(
            "🛠 Tools & Resources:\n"
            "- Guides for online business\n"
            "- Productivity tools\n"
            "- Telegram bot tips",
            reply_markup=back_button
        )
    elif query.data == 'updates':
        await query.edit_message_text(
            "📈 Updates & Tips:\n"
            "- New earning methods\n"
            "- Latest TON wallet updates\n"
            "- Telegram platform news",
            reply_markup=back_button
        )
    elif query.data == 'main':
        # Return to main menu
        await query.edit_message_text(
            "Main Menu:",
            reply_markup=main_menu_keyboard()
        )

# Build the bot application
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))

# Run the bot
app.run_polling()
