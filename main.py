import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging

API_TOKEN = '7211206928:AAF2EA_PLC5zUlPwvxWh4WGiX_uWTU2RBcs'  # Replace with your BotFather token

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Connect to database
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    referrer INTEGER,
    invited INTEGER DEFAULT 0
)
''')
conn.commit()

# --- Keyboards ---
def main_menu():
    buttons = [
        [InlineKeyboardButton("📊 Balance", callback_data="balance")],
        [InlineKeyboardButton("📝 Tasks", callback_data="tasks")],
        [InlineKeyboardButton("🧑‍🤝‍🧑 Invite Friends", callback_data="invite")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Commands ---
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()
    
    # Register user
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        ref = int(args) if args.isdigit() else None
        cursor.execute("INSERT INTO users (user_id, referrer) VALUES (?, ?)", (user_id, ref))
        conn.commit()
        
        # Give referrer bonus
        if ref:
            cursor.execute("UPDATE users SET balance = balance + 0.5, invited = invited + 1 WHERE user_id = ?", (ref,))
            conn.commit()

    await message.answer(
        f"👋 Welcome to EarnEasyBot!\n\nUse the menu below to start earning rewards.",
        reply_markup=main_menu()
    )

# --- Callbacks ---
@dp.callback_query_handler(lambda c: c.data == 'balance')
async def check_balance(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    await call.message.edit_text(f"💰 Your current balance: ${balance:.2f}", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == 'tasks')
async def do_tasks(call: types.CallbackQuery):
    user_id = call.from_user.id
    # Simulate a task (in real use, link to external tasks or verify actions)
    cursor.execute("UPDATE users SET balance = balance + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    await call.message.edit_text("✅ Task completed! $1 added to your balance.", reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == 'invite')
async def invite_friends(call: types.CallbackQuery):
    user_id = call.from_user.id
    link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
    cursor.execute("SELECT invited FROM users WHERE user_id = ?", (user_id,))
    invited = cursor.fetchone()[0]
    await call.message.edit_text(
        f"👥 Invite your friends using this link:\n\n{link}\n\n"
        f"You have invited: {invited} user(s).\n"
        f"Earn $0.50 per referral!",
        reply_markup=main_menu()
    )

@dp.callback_query_handler(lambda c: c.data == 'withdraw')
async def request_withdraw(call: types.CallbackQuery):
    user_id = call.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]

    if balance >= 20:
        await call.message.edit_text("💸 Withdrawal requested! The admin will review your request.", reply_markup=main_menu())
        # (Admin notification logic can be added here)
    else:
        await call.message.edit_text(f"❌ You need at least $20 to withdraw. Your balance is ${balance:.2f}", reply_markup=main_menu())

# --- Run Bot ---
if name == 'main':
    executor.start_polling(dp, skip_updates=True)
