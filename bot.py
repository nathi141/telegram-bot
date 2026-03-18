from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes
import requests
import sqlite3

TOKEN = "8777576356:AAFnb1i2VXgWYum8Ridy20KWhIO-Ey1QV9g"  # <-- Replace this only
TON_WALLET = "UQA3K4E_p7Jha0foZ8Pf1WUIxRHebfRiDzX94NUV-3nyZmzf"
TON_API_KEY = "41d6584cbce3d9d50c0ca67e38becfe1154236dfe27a7ff8f0992e2b7c613ace"
ADMIN_IDS = ["8366726152", "6502235975"]  # Your Telegram IDs
# ====================

# ===== DATABASE SETUP =====
conn = sqlite3.connect('botdata.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id TEXT PRIMARY KEY,
    balance REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS referrals(
    referrer_id TEXT,
    count INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS ads(
    ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    text TEXT,
    link TEXT,
    amount REAL,
    status TEXT DEFAULT 'pending'
)
""")
conn.commit()
# ==========================

# ===== MAIN MENU =====
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💸 Earn Money", callback_data='earn')],
        [InlineKeyboardButton("👥 My Referrals", callback_data='ref')],
        [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📢 Ads", callback_data='ads')],
        [InlineKeyboardButton("🛠 Tools", callback_data='tools')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    # Add user to DB
    cursor.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    conn.commit()

    # Check referral code
    if context.args:
        referrer_id = context.args[0]
        if referrer_id != user_id:
            cursor.execute("INSERT OR IGNORE INTO referrals(referrer_id,count) VALUES(?,0)", (referrer_id,))
            cursor.execute("UPDATE referrals SET count = count + 1 WHERE referrer_id=?", (referrer_id,))
            conn.commit()

    welcome_text = (
        "🎉 Welcome to BizBoostPro!\n\n"
        "Earn money, manage your wallet, and run ads easily.\n\n"
        "Choose an option below 👇"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

# ===== BUTTON HANDLER =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Main Menu", callback_data='main')]])

    # ----- EARN -----
    if query.data == 'earn':
        referral_link = f"https://t.me/BizBoostProBot?start={user_id}"
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]
        await query.edit_message_text(
            f"💸 Earn Money\n\n"
            f"Your Balance: {balance} TON\n"
            f"Invite people using your link:\n{referral_link}\n\n"
            f"You earn rewards for every person that joins!",
            reply_markup=back_btn
        )

    # ----- REFERRALS -----
    elif query.data == 'ref':
        cursor.execute("SELECT count FROM referrals WHERE referrer_id=?", (user_id,))
        row = cursor.fetchone()
        count = row[0] if row else 0
        await query.edit_message_text(
            f"👥 Your Referrals: {count}\n\nKeep inviting to earn more 💸",
            reply_markup=back_btn
        )

    # ----- WALLET -----
    elif query.data == 'wallet':
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]
        await query.edit_message_text(
            f"💰 Your Wallet Balance: {balance} TON\n\n"
            f"Wallet Address:\n{TON_WALLET}",
            reply_markup=back_btn
        )

    # ----- ADS -----
    elif query.data == 'ads':
        await update.message.reply_text("📢 Send your Ad TEXT:", reply_markup=None)
        context.user_data['ads_stage'] = 'text'

    # ----- TOOLS -----
    elif query.data == 'tools':
        await update.message.reply_text(
            "🛠 Tools & Resources coming soon...",
            reply_markup=back_btn
        )

    # ----- MAIN MENU -----
    elif query.data == 'main':
        await query.edit_message_text("🏠 Main Menu", reply_markup=main_menu_keyboard())

# ===== MESSAGE HANDLER FOR ADS & DEPOSITS =====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    # Handle Ads Submission
    if context.user_data.get('ads_stage') == 'text':
        context.user_data['ad_text'] = text
        await update.message.reply_text("🔗 Send your Ad LINK")
        context.user_data['ads_stage'] = 'link'
        return

    if context.user_data.get('ads_stage') == 'link':
        context.user_data['ad_link'] = text
        await update.message.reply_text("💰 Enter budget amount in TON")
        context.user_data['ads_stage'] = 'budget'
        return

    if context.user_data.get('ads_stage') == 'budget':
        try:
            amount = float(text)
        except:
            await update.message.reply_text("Please enter a valid number for the budget.")
            return

        # Check balance
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]
        if balance < amount:
            await update.message.reply_text("❌ Insufficient balance. Please deposit TON first.")
            context.user_data['ads_stage'] = None
            return

        # Deduct balance
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id))
        conn.commit()

        # Save ad
        cursor.execute("INSERT INTO ads(user_id, text, link, amount) VALUES(?,?,?,?)",
                       (user_id, context.user_data['ad_text'], context.user_data['ad_link'], amount))
        conn.commit()

        # Send to admins
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(admin_id, f"📢 New Ad Submitted by {user_id}\n\n"
                                                     f"{context.user_data['ad_text']}\n{context.user_data['ad_link']}\n💰 Budget: {amount} TON\n"
                                                     f"✅ Click approve to post", reply_markup=None)

        await update.message.reply_text("✅ Ad submitted for approval.")
        context.user_data['ads_stage'] = None
        return

# ===== AUTO TON BALANCE UPDATE =====
def update_balances_from_ton_api():
    """
    Auto-update user balances using TON API
    """
    try:
        res = requests.get(
            f"https://tonapi.io/v2/accounts/balance?account={TON_WALLET}",
            headers={"x-api-key": TON_API_KEY}
        )
        data = res.json()
        balance = float(data.get("balance", 0))
        # Optional: distribute new funds to users/referrals if needed
        # This function can be run periodically with a scheduler
    except Exception as e:
        print("Error updating TON balance:", e)

# ===== ADMIN DASHBOARD =====
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied")
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ads WHERE status='pending'")
    pending_ads = cursor.fetchone()[0]

    await update.message.reply_text(
        f"📊 Admin Dashboard\n\n"
        f"Total Users: {total_users}\n"
        f"Total Balance: {total_balance} TON\n"
        f"Pending Ads: {pending_ads}"
    )

# ===== BUILD BOT =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(CommandHandler("admin", admin_dashboard))
app.add_handler(CommandHandler("dashboard", admin_dashboard))
app.add_handler(CommandHandler("menu", start))
app.add_handler(MessageHandler(None, message_handler))

# ===== RUN BOT =====
app.run_polling()
