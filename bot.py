import os
import mysql.connector
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "telegram.bot")

user_status = {}

def simpan_nomor(nomor):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO nomor_jual (nomor) VALUES (%s)", (nomor,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_status[update.effective_user.id] = "menu"
    menu = ReplyKeyboardMarkup(
        [["1. Masukkan nomor yang Anda jual"]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Selamat datang di MyStore Bot 👋\nSilakan pilih menu di bawah ini.",
        reply_markup=menu
    )

async def terima_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    teks = update.message.text.strip()
    if teks == "1. Masukkan nomor yang Anda jual":
        user_status[user_id] = "tunggu_nomor"
        await update.message.reply_text(
            "Silakan masukkan nomor yang Anda jual\n(contoh: 6281234567890)"
        )
    elif user_status.get(user_id) == "tunggu_nomor":
        if teks.isdigit() and len(teks) >= 10:
            berhasil = simpan_nomor(teks)
            if berhasil:
                user_status[user_id] = "menu"
                menu = ReplyKeyboardMarkup(
                    [["1. Masukkan nomor yang Anda jual"]],
                    resize_keyboard=True
                )
                await update.message.reply_text(
                    f"✅ Berhasil!\nNomor {teks} telah disimpan ke database.\n\nSilakan pilih menu di bawah ini.",
                    reply_markup=menu
                )
            else:
                await update.message.reply_text("❌ Gagal menyimpan nomor. Coba lagi.")
        else:
            await update.message.reply_text(
                "⚠️ Nomor tidak valid!\nMasukkan nomor HP yang benar.\nContoh: 6281234567890"
            )
    else:
        await update.message.reply_text("Silakan ketik /start untuk memulai.")

print("Bot sedang berjalan...")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, terima_pesan))
app.run_polling()
