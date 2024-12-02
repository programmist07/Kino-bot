import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import requests

TOKEN = "Token here"
channel_link = "link"
users_file = "users.json"

async def load_users():
    try:
        with open(users_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Xatolik: Foydalanuvchilarni yuklashda muammo - {e}")
        return {}

async def save_users(users):
    try:
        with open(users_file, "w") as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        print(f"Xatolik: Foydalanuvchilarni saqlashda muammo - {e}")

async def add_user(user_id, username, full_name, phone_number=None):
    try:
        users = await load_users()
        if str(user_id) not in users:
            users[str(user_id)] = {
                "username": username,
                "full_name": full_name,
                "phone_number": phone_number
            }
            await save_users(users)
    except Exception as e:
        print(f"Xatolik: Foydalanuvchini qo'shishda muammo - {e}")

async def is_user_registered(user_id):
    try:
        users = await load_users()
        return str(user_id) in users
    except Exception as e:
        print(f"Xatolik: Ro'yxatni tekshirishda muammo - {e}")
        return False


async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        user_id = update.effective_user.id
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={channel_link}&user_id={user_id}"
        response = requests.get(url).json()
        if response.get("ok"):
            status = response.get("result", {}).get("status", "")
            return status in ("member", "administrator", "creator")
        return False
    except Exception as e:
        print(f"Xatolik: Obunani tekshirishda muammo - {e}")
        return False


async def channel_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user.full_name
        inline_buttons = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{channel_link}")],
            [InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")]
        ]
        buttons = InlineKeyboardMarkup(inline_buttons)
        await update.message.reply_text(f"Salom {user}!\nBotdan foydalanish uchun kanalimizga obuna bo'ling:", reply_markup=buttons)
    except Exception as e:
        print(f"Xatolik: Kanal tugmachalarini jo'natishda muammo - {e}")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        if query.data == "check_subscription":
            obuna = await is_subscribed(update, context)
            if obuna:
                await query.answer("Obunangiz tasdiqlandi!")
                await context.bot.send_message(chat_id=update.effective_user.id, text="Endi botdan foydalanishingiz mumkin.")
            else:
                await query.answer("Iltimos, obuna bo'ling!", show_alert=True)
    except Exception as e:
        print(f"Xatolik: Callback query ishlovida muammo - {e}")

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.reply_text(
            text="Telefon raqamingizni ulashing:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📞 Telefon raqamini ulash", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    except Exception as e:
        print(f"Xatolik: Ro'yxatdan o'tishda muammo - {e}")


async def save_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        contact = update.message.contact
        user_id = update.effective_user.id
        username = update.effective_user.username
        full_name = update.effective_user.full_name
        phone_number = contact.phone_number

        await add_user(user_id, username, full_name, phone_number)
        await update.message.reply_text("Siz muvaffaqiyatli ro'yxatdan o'tdingiz!")
    except Exception as e:
        print(f"Xatolik: Kontaktni saqlashda muammo - {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_id = update.effective_user.id
        message = update.message.text

        if not await is_subscribed(update, context):
            await channel_buttons(update, context)
        elif not await is_user_registered(user_id):  # `await` qo'shildi
            await register_user(update, context)
        else:
            if message == "1":
                await update.message.reply_text("Kino: Turtles\nHavola: https://youtu.be/YxJiPpJWoRE")
            elif message == "2":
                await update.message.reply_text("Kino: Kung Fu Panda\nHavola: https://youtu.be/l6gRylHsyR4")
            else:
                await update.message.reply_text("Kechirasiz, bunday kino mavjud emas.")
    except Exception as e:
        print(f"Xatolik: Xabarlarni boshqarishda muammo - {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        await update.message.reply_text(f"Salom {user.first_name}!")
        if not await is_user_registered(user.id):  # `await` qo'shildi
            await register_user(update, context)
        else:
            await update.message.reply_text("Siz allaqachon ro'yxatdan o'tgansiz.")
    except Exception as e:
        print(f"Xatolik: Start buyruqda muammo - {e}")


if __name__ == "__main__":
    try:
        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.CONTACT, save_contact))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(handle_callback_query))

        print("Bot ishlayapti...")
        app.run_polling()
    except Exception as e:
        print(f"Xatolik: Botni ishga tushirishda muammo - {e}")
