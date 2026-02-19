import telebot
import logging
import traceback
import os
from groq import Groq
from database import init_db, query_db 
from error_notifier import send_error_notification
from dotenv import load_dotenv

# --- 1. KONFIGURASI ---
load_dotenv()
logging.basicConfig(
    filename='error_log.txt',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

# --- 2. STATE & DATABASE ---
user_ai_sessions = {}

try:
    init_db()
except Exception as e:
    print(f"Database Warning: {e}")

SYSTEM_PROMPT = """
Kamu adalah Asisten Customer Service dari 'DigiEco', toko produk digital.
Gaya bicaramu: Profesional, ramah, dan membantu.
Tugasmu: Menjawab pertanyaan umum seputar teknologi, coding, dan produk digital.
Jika ditanya stok spesifik, arahkan user menggunakan perintah /list_produk.
Jawablah dengan ringkas (maksimal 3 paragraf).
"""

# --- 3. HANDLER COMMAND (WAJIB DI ATAS) ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    nama_user = message.from_user.first_name
    teks = (
        f"👋 Halo, {nama_user}!\n"
        "Selamat datang di DigiEco Assistant.\n\n"
        "🤖 *Fitur AI Chat:*\n"
        "Ketik /ai untuk mode ngobrol.\n"
        "Ketik /stop untuk berhenti.\n\n"
        "Gunakan perintah:\n"
        "🛍️ `/list_produk` - Katalog & stok\n"
        "🕒 `/jam_kerja` - Operasional\n"
        "📞 `/kontak` - Admin\n\n"
        # "🔧 Admin:\n"
        # "`/tambah_stok` - Update stok" 
    )
    bot.reply_to(message, teks, parse_mode='Markdown')

@bot.message_handler(commands=['ai'])
def start_ai_mode(message):
    user_ai_sessions[message.chat.id] = True
    bot.reply_to(message, "🤖 *Mode AI Aktif!*\n(Ketik /stop untuk keluar)", parse_mode='Markdown')

@bot.message_handler(commands=['stop'])
def stop_ai_mode(message):
    user_ai_sessions[message.chat.id] = False
    bot.reply_to(message, "🛑 Mode AI dinonaktifkan.")

@bot.message_handler(commands=['jam_kerja'])
def cek_jam(message):
    try:
        hasil = query_db("SELECT isi FROM info WHERE kunci='jam_kerja'", fetch=True)
        jawaban = hasil[0][0] if hasil else "09.00 - 17.00 WIB"
        bot.reply_to(message, f"🕒 Jam Operasional: {jawaban}")
    except Exception as e:
        logging.error(f"DB Error: {e}")

@bot.message_handler(commands=['kontak'])
def cek_kontak(message):
    try:
        hasil = query_db("SELECT isi FROM info WHERE kunci='kontak'", fetch=True)
        jawaban = hasil[0][0] if hasil else "@admin_digieco"
        bot.reply_to(message, f"📞 Hubungi: {jawaban}")
    except Exception as e:
        logging.error(f"DB Error: {e}")

@bot.message_handler(commands=['list_produk'])
def cek_katalog(message):
    try:
        data = query_db("SELECT nama_produk, stok, harga FROM produk", fetch=True)
        if not data:
            bot.reply_to(message, "Belum ada produk digital tersedia.")
            return

        respon = "📂 *KATALOG DIGIECO:*\n"
        for item in data:
            nama, stok, harga = item
            status = "✅ Ready" if stok > 0 else "❌ Habis"
            respon += f"\n📦 *{nama}*\n 💰 Rp{harga:,}\n 📊 Stok: {stok} ({status})\n"
        
        bot.send_message(message.chat.id, respon, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"DB Error: {e}")

@bot.message_handler(commands=['tambah_stok'])
def update_stok_start(message):
    msg = bot.reply_to(message, "📝 Format: Nama Produk, Jumlah (Contoh: Ebook Python, 10)")
    bot.register_next_step_handler(msg, update_stok_save)

def update_stok_save(message):
    try:
        if ',' not in message.text:
            bot.reply_to(message, "❌ Gunakan koma sebagai pemisah. Contoh: Ebook, 10")
            return
            
        nama_input, jumlah_input = message.text.split(',')
        nama = nama_input.strip()
        jumlah = int(jumlah_input.strip())
        
        cek = query_db("SELECT id FROM produk WHERE nama_produk = ?", (nama,), fetch=True)
        if cek:
            query_db("UPDATE produk SET stok = stok + ? WHERE nama_produk = ?", (jumlah, nama))
            bot.reply_to(message, f"✅ Stok *{nama}* ditambah {jumlah}.", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"⚠️ Produk *{nama}* tidak ditemukan.", parse_mode='Markdown')
    except ValueError:
        bot.reply_to(message, "❌ Jumlah harus berupa angka.")
    except Exception as e:
        bot.reply_to(message, "❌ Terjadi error saat update.")
        logging.error(f"Stock Update Error: {e}")

@bot.message_handler(commands=['getid'])
def get_id(message):
    bot.reply_to(message, f"Chat ID Anda: {message.chat.id}")

# --- 4. HANDLER TEKS / AI (WAJIB PALING BAWAH) ---

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    chat_id = message.chat.id
    
    # Hanya respon jika user sedang dalam Mode AI
    if user_ai_sessions.get(chat_id):
        pertanyaan = message.text
        bot.send_chat_action(chat_id, 'typing')

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": pertanyaan}
                ],
                model="llama-3.3-70b-versatile",
            )
            jawaban = chat_completion.choices[0].message.content
            bot.reply_to(message, jawaban)

        except Exception as e:
            bot.reply_to(message, "⚠️ AI sedang gangguan. Coba lagi nanti.")
            logging.error(f"Groq Error: {str(e)}")
    else:
        # Jika bukan command dan bukan mode AI, abaikan
        pass 

# --- RUN ---
print("Bot DigiEco + AI berjalan dengan urutan handler yang diperbaiki...")
bot.infinity_polling()