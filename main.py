import asyncio
import logging
import sys
import config
from telegram_client import ShpBotAdapter
from storage import OutputWriter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler(config.LOGS_DIR / "run.log", encoding="utf-8"), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class MissionCheckerApp:
    def __init__(self):
        self.adapter = ShpBotAdapter(str(config.SESSIONS_DIR / "shp_checker"))
        self.writer = OutputWriter(config.OUTPUT_DIR)
        self.is_running = False
        self.stats = {"total": 0, "processed": 0, "coin": 0, "other": 0}

    async def run_mission(self):
        try:
            with open("targets.txt", "r", encoding="utf-8") as f:
                targets = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error("targets.txt tidak ditemukan.")
            return

        if not targets:
            logger.error("targets.txt kosong.")
            return

        self.stats = {"total": len(targets), "processed": 0, "coin": 0, "other": 0}
        self.is_running = True
        logger.info(f"Memulai cek untuk {len(targets)} target...")
        await self.adapter.connect()

        try:
            for i, target in enumerate(targets, 1):
                logger.info(f"[{i}/{len(targets)}] Memproses: {target}")
                result = await self.adapter.check_target(target)
                await self.writer.write_result(result)
                
                if result.category == "coin":
                    self.stats["coin"] += 1
                else:
                    self.stats["other"] += 1
                
                self.stats["processed"] += 1
                if i < len(targets):
                    await asyncio.sleep(config.BATCH_DELAY)
        finally:
            await self.adapter.disconnect()
            self.is_running = False
            logger.info(f"Selesai. Berhasil: {self.stats['coin']}, Other: {self.stats['other']}")

    async def menu(self):
        print("\n=== MENU ===")
        print("/mission - Mulai Bulk Check")
        print("/status  - Lihat Progres")
        print("/stop    - Stop")
        print("/exit    - Keluar")
        while True:
            cmd = await asyncio.get_event_loop().run_in_executor(None, input, "\nPerintah > ")
            if cmd == "/mission":
                if not self.is_running: await self.run_mission()
                else: print("Sedang berjalan!")
            elif cmd == "/status":
                print(f"Total: {self.stats['total']} | Selesai: {self.stats['processed']} | Coin: {self.stats['coin']} | Other: {self.stats['other']}")
            elif cmd == "/exit":
                break

async def main():
    config.ensure_dirs()
    await MissionCheckerApp().menu()

if __name__ == "__main__":
    asyncio.run(main())