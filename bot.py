import asyncio
from telethon import TelegramClient, events
import redis

# 🔥 GANTI DENGAN DATA BOT LO
API_ID = 1234567
API_HASH = "abcd1234efgh5678ijkl"
BOT_TOKEN = "YOUR_BOT_TOKEN"

# 🔥 GANTI DENGAN ID CHANNEL LO
CHANNEL_IMAGES = -1001234567890
CHANNEL_VIDEOS = -1009876543210

# 🔥 KONEKSI TELEGRAM & REDIS
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# ✅ AUTO FORWARD FILE BERDASARKAN KATEGORI
@client.on(events.NewMessage(incoming=True))
async def process_file(event):
    if not event.message.media:
        return

    # 🔥 AMBIL HASH FILE SESUAI JENIS MEDIA
    if event.message.photo:
        file_hash = str(event.message.photo.id)
        category = "image"
    elif event.message.video:
        file_hash = str(event.message.video.id)
        category = "video"
    elif event.message.document:
        file_hash = str(event.message.document.id)
        category = "document"
    else:
        return  # Skip kalau bukan media

    # 🔥 CEK APAKAH FILE SUDAH ADA DI DATABASE
    if r.setnx(f"file:{file_hash}", "used"):  
        r.expire(f"file:{file_hash}", 86400)  # Simpan hash 24 jam  
        target_channel = CHANNEL_IMAGES if category == "image" else CHANNEL_VIDEOS

        caption = f"📂 **Kategori:** {category.upper()}\n🆔 **Dari:** @{event.sender.username or 'Unknown'}"
        await client.forward_messages(target_channel, event.message)
        await client.send_message(target_channel, caption)

        r.incr(f"stats:{category}")
        await event.reply("✅ File baru terdeteksi!\n" + caption)

    else:
        r.incr("stats:duplicates")
        await event.reply("❌ File sudah ada di database, skip!")

# ✅ PERINTAH /STATS BUAT CEK STATISTIK REAL-TIME
@client.on(events.NewMessage(pattern="/stats"))
async def show_stats(event):
    images = int(r.get("stats:image") or 0)
    videos = int(r.get("stats:video") or 0)
    duplicates = int(r.get("stats:duplicates") or 0)

    message = f"📊 **Statistik File (Real-Time):**\n📸 Images: {images} files\n🎥 Videos: {videos} files\n\n🗑️ File duplikat yang dihapus: {duplicates} file"
    await event.reply(message)

# ✅ PERINTAH /LINK BUAT AKSES SUBCHANNEL
@client.on(events.NewMessage(pattern="/link"))
async def send_links(event):
    message = "🔗 **Akses Subchannel**:\n"
    message += f"📸 **Semua file image ada di sini:** [Klik aja](https://t.me/your_channel_images)\n"
    message += f"🎥 **Semua file video ada di sini:** [Klik aja](https://t.me/your_channel_videos)"
    await event.reply(message, link_preview=False)

# 🔥 JALANKAN BOT
print("🚀 Bot sudah aktif!")
client.run_until_disconnected()
