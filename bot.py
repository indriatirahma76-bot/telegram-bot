import sys
print(f"Python version: {sys.version}")
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

def koneksi():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def cek_terdaftar(telegram_id):
    try:
        conn = koneksi()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pengguna WHERE telegram_id = %s", (telegram_id,))
        hasil = cursor.fetchone()
        conn.close()
        return hasil
    except Exception as e:
        print(f"Error: {e}")
        return None

def simpan_pengguna(telegram_id, id_digipos, nama, nomor_hp):
    try:
        conn = koneksi()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pengguna (telegram_id, id_digipos, nama, nomor_hp) VALUES (%s, %s, %s, %s)",
            (telegram_id, id_digipos, nama, nomor_hp)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def simpan_nomor(nomor, id_digipos, nama_pelapor):
    try:
        conn = koneksi()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO nomor_jual (nomor, id_digipos, nama_pelapor) VALUES (%s, %s, %s)",
            (nomor, id_digipos, nama_pelapor)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    pengguna = cek_terdaftar(telegram_id)

    if pengguna:
        user_status[telegram_id] = "menu"
        nama = pengguna[2]
        menu = ReplyKeyboardMarkup(
            [["1. Laporkan Nomor HP"]],
            resize_keyboard=True
        )
        await update.message.reply_text(
            f"Selamat datang kembali {nama}! 👋\nSilakan pilih menu di bawah ini.",
            reply_markup=menu
        )
    else:
        user_status[telegram_id] = "daftar_id_digipos"
        await update.message.reply_text(
            "Selamat datang! 👋\nAnda belum terdaftar.\n\nSilakan registrasi dulu.\n\nMasukkan ID Digipos Anda:"
        )

async def terima_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    teks = update.message.text.strip()
    status = user_status.get(telegram_id, "")

    if status == "daftar_id_digipos":
        context.user_data["id_digipos"] = teks
        user_status[telegram_id] = "daftar_nama"
        await update.message.reply_text("Masukkan nama Anda:")

    elif status == "daftar_nama":
        context.user_data["nama"] = teks
        user_status[telegram_id] = "daftar_nomor_hp"
        await update.message.reply_text("Masukkan nomor HP Anda:")

    elif status == "daftar_nomor_hp":
        context.user_data["nomor_hp"] = teks
        id_digipos = context.user_data["id_digipos"]
        nama = context.user_data["nama"]
        nomor_hp = teks

        berhasil = simpan_pengguna(telegram_id, id_digipos, nama, nomor_hp)
        if berhasil:
            user_status[telegram_id] = "menu"
            menu = ReplyKeyboardMarkup(
                [["1. Laporkan Nomor HP"]],
                resize_keyboard=True
            )
            await update.message.reply_text(
                f"✅ Registrasi berhasil!\nSelamat datang {nama}!\n\nSilakan pilih menu di bawah ini.",
                reply_markup=menu
            )
        else:
            await update.message.reply_text("❌ Gagal registrasi. Coba lagi dengan /start")

    elif teks == "1. Laporkan Nomor HP":
        user_status[telegram_id] = "tunggu_nomor"
        await update.message.reply_text(
            "Masukkan nomor HP yang ingin dilaporkan:\n(contoh: 6281234567890)"
        )

    elif status == "tunggu_nomor":
        if teks.isdigit() and len(teks) >= 10:
            pengguna = cek_terdaftar(telegram_id)
            id_digipos = pengguna[1]
            nama_pelapor = pengguna[2]

            berhasil = simpan_nomor(teks, id_digipos, nama_pelapor)
            if berhasil:
                user_status[telegram_id] = "menu"
                menu = ReplyKeyboardMarkup(
                    [["1. Laporkan Nomor HP"]],
                    resize_keyboard=True
                )
                await update.message.reply_text(
                    f"✅ Berhasil!\nNomor {teks} telah dilaporkan!\n\nSilakan pilih menu di bawah ini.",
                    reply_markup=menu
                )
            else:
                await update.message.reply_text("❌ Gagal melaporkan nomor. Coba lagi.")
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
