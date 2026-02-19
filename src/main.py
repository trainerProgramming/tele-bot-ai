import telebot
import os
from dotenv import load_dotenv

load_dotenv()

# Ambil dari environment variable
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def send_error_notification(error_message):
    try:
        pesan = (
            "🚨 *ERROR TERDETEKSI DI DIGIECO BOT*\n\n"
            f"{error_message}"
        )
        bot.send_message(ADMIN_CHAT_ID, pesan, parse_mode='Markdown')
    except Exception as e:
        print("Gagal mengirim notifikasi error:", e)
