import sys
print(f"Python version: {sys.version}")
import os
import mysql.connector
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "telegram.bot")

ADMIN_ID = 7356928799

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
        cursor.execute("SELECT * FROM pengguna WHERE telegram_id = %s AND status = 'approved'", (telegram_id,))
        hasil = cursor.fetchone()
        conn.close()
        return hasil
    except Exception as e:
        print(f"Error: {e}")
        return None

def cek_pending(telegram_id):
    try:
        conn = koneksi()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pengguna WHERE telegram_id = %s AND status = 'pending'", (telegram_id,))
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
            "INSERT INTO pengguna (telegram_id, id_digipos, nama, nomor_hp, status) VALUES (%s, %s, %s, %s, 'pending')",
            (telegram_id, id_digipos, nama, nomor_hp)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def update_status(telegram_id, status):
    try:
        conn = koneksi()
        cursor = conn.cursor()
        cursor.execute("UPDATE pengguna SET status = %s WHERE telegram_id = %s", (status, telegram_id))
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
    pending = cek_pending(telegram_id)

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
    elif pending:
        await update.message.reply_text(
            "⏳ Registrasi kamu sedang menunggu persetujuan admin.\nSabar ya! 😊"
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
            user_status[telegram_id] = "menunggu"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Setuju", callback_data=f"setuju_{telegram_id}"),
                 InlineKeyboardButton("❌ Tolak", callback_data=f"tolak_{telegram_id}")]
            ])
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📋 Ada pendaftaran baru!\n\nNama: {nama}\nID Digipos: {id_digipos}\nHP: {nomor_hp}",
                reply_markup=keyboard
            )
            await update.message.reply_text(
                "✅ Registrasi berhasil dikirim!\nTunggu persetujuan admin ya. 😊"
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

async def tombol_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("setuju_"):
        telegram_id = int(data.split("_")[1])
        update_status(telegram_id, "approved")
        await query.edit_message_text("✅ Pendaftaran disetujui!")
        menu = ReplyKeyboardMarkup(
            [["1. Laporkan Nomor HP"]],
            resize_keyboard=True
        )
        await context.bot.send_message(
            chat_id=telegram_id,
            text="✅ Registrasi kamu telah disetujui admin!\nSilakan pilih menu di bawah ini.",
            reply_markup=menu
        )

    elif data.startswith("tolak_"):
        telegram_id = int(data.split("_")[1])
        update_status(telegram_id, "ditolak")
        await query.edit_message_text("❌ Pendaftaran ditolak!")
        await context.bot.send_message(
            chat_id=telegram_id,
            text="❌ Maaf, registrasi kamu ditolak oleh admin."
        )

print("Bot sedang berjalan...")
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, terima_pesan))
app.add_handler(CallbackQueryHandler(tombol_admin))
app.run_polling()
