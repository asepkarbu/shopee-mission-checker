from telethon import TelegramClient
import config

async def main():
    print("Memulai proses login manual...")
    client = TelegramClient(str(config.SESSIONS_DIR / "shp_checker"), config.API_ID, config.API_HASH)
    
    # Fungsi start() ini akan menahan program sampai Anda memasukkan OTP dengan benar
    await client.start()
    
    print("\n✅ LOGIN BERHASIL! Sesi telah disimpan.")
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())