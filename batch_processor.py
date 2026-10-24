"""Pemrosesan batch async: antrean, konkurensi terbatas, backoff FloodWait, resume."""
import asyncio
import logging
from pathlib import Path
from typing import Optional

import config
from parser import MissionResult
from storage import OutputWriter
from telegram_client import ShpBotAdapter

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self, targets: list[str], adapter: ShpBotAdapter, writer: OutputWriter):
        self.targets = targets
        self.adapter = adapter
        self.writer = writer
        self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY)
        self.stop_requested = False
        self.stats = {"total": len(targets), "done": 0, "coin": 0, "other": 0, "error": 0}
        self._processed: list[str] = []

    def request_stop(self):
        self.stop_requested = True

    async def process_one(self, target: str):
        async with self.semaphore:
            if self.stop_requested:
                return
            try:
                result = await self.adapter.check_target(target)
                if result.raw_text.startswith("TIMEOUT") or result.raw_text.startswith("ERROR"):
                    await self.writer.write_result(result, error_text=result.raw_text[:100])
                    self.stats["error"] += 1
                else:
                    await self.writer.write_result(result)
                    if result.category == "coin":
                        self.stats["coin"] += 1
                    else:
                        self.stats["other"] += 1
                self._processed.append(target)
                self.stats["done"] += 1
            except Exception as e:
                logger.error(f"{target}: pemrosesan gagal: {e}")
                await self.writer.write_result(
                    MissionResult(target, "other", f"ERROR: {e}"),
                    error_text=str(e)[:100]
                )
                self.stats["error"] += 1
                self._processed.append(target)
                self.stats["done"] += 1

    async def run(self) -> dict:
        """Jalankan semua target, tampilkan progres setiap SAVE_INTERVAL."""
        pending = [t for t in self.targets if t not in self.writer.store.load_processed_ids("coin.txt")]
        
        tasks = []
        for i, target in enumerate(pending):
            if self.stop_requested:
                break
            tasks.append(asyncio.create_task(self.process_one(target)))
            # Jeda untuk menghindari pengiriman berlebihan
            if i < len(pending) - 1:
                await asyncio.sleep(config.BATCH_DELAY)

        await asyncio.gather(*tasks, return_exceptions=True)

        # Simpan progres
        await self.writer.store.save_progress(self._processed)
        return self.stats