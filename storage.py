import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class AsyncFileStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._locks: dict[Path, asyncio.Lock] = {}
        self._seen: set[str] = set()

    def _lock_for(self, path: Path) -> asyncio.Lock:
        if path not in self._locks:
            self._locks[path] = asyncio.Lock()
        return self._locks[path]

    async def append_line(self, filename: str, line: str, identifier: Optional[str] = None):
        path = self.base_dir / filename
        if identifier and identifier in self._seen:
            return
        async with self._lock_for(path):
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        if identifier:
            self._seen.add(identifier)

    def load_processed_ids(self, filename: str) -> set[str]:
        return set()

    async def save_progress(self, processed: list[str], filename: str = ".progress.json"):
        path = self.base_dir / filename
        async with self._lock_for(path):
            data = {"processed": processed, "updated": datetime.now(timezone.utc).isoformat()}
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load_progress(self, filename: str = ".progress.json") -> set[str]:
        path = self.base_dir / filename
        if not path.exists():
            return set()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return set(data.get("processed", []))
        except Exception:
            return set()

class OutputWriter:
    def __init__(self, base_dir: Path):
        self.store = AsyncFileStore(base_dir)

    async def write_result(self, result, error_text: Optional[str] = None):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        if error_text:
            line = f"[{ts}] {result.target}\tERROR: {error_text}"
            await self.store.append_line("errors.txt", line, result.identifier)
            return
            
        if result.category == "coin":
            detail_parts = []
            for m in result.missions:
                detail_parts.append(f"{m['name']} ({m['coins']} koin) - {m['status']}")
            detail_str = " | ".join(detail_parts)
            line = f"[{ts}] {result.target}\n   -> {detail_str}"
            await self.store.append_line("coin.txt", line, result.identifier)
        else:
            preview = result.raw_text.replace("\n", " ")[:150]
            line = f"[{ts}] {result.target}\t{preview}"
            await self.store.append_line("other.txt", line, result.identifier)