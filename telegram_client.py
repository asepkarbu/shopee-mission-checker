import asyncio
import logging
from typing import Optional
from telethon import TelegramClient, errors
import config
from parser import parse_response, MissionResult, is_error_response

logger = logging.getLogger(__name__)

class ShpBotAdapter:
    def __init__(self, session_path: str):
        self.session_path = session_path
        self.client: Optional[TelegramClient] = None

    async def connect(self):
        if config.API_ID == 0 or not config.API_HASH:
            raise ValueError("API ID/HASH belum diatur")
        self.client = TelegramClient(self.session_path, config.API_ID, config.API_HASH)
        await self.client.start()
        logger.info("Klien Telegram terhubung")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            logger.info("Klien Telegram terputus")

    async def check_target(self, target: str) -> MissionResult:
        if not self.client: raise RuntimeError("Klien belum terhubung")
        raw_text = ""
        try:
            async with self.client.conversation(config.BOT_USERNAME, timeout=config.RESPONSE_TIMEOUT) as conv:
                await conv.send_message("/mission")
                response = await conv.get_response()
                
                if response.reply_markup and response.reply_markup.rows:
                    for row in response.reply_markup.rows:
                        for button in row.buttons:
                            if "checkin" in button.text.lower():
                                await response.click(text=button.text)
                                break
                                
                response = await conv.get_response()
                if response.reply_markup and response.reply_markup.rows:
                    for row in response.reply_markup.rows:
                        for button in row.buttons:
                            if "email" in button.text.lower() or "username" in button.text.lower():
                                await response.click(text=button.text)
                                break

                await conv.get_response() 
                await conv.send_message(target)
                
                logger.info(f"⏳ [{target}] Menunggu 20 detik. Silakan isi PIN di Telegram jika diminta...")
                await asyncio.sleep(30)
                
                raw_text = ""
                for _ in range(5):
                    try:
                        response = await conv.get_response(timeout=10)
                        teks = response.text or ""
                        if "Misi Checkin" in teks or "koin" in teks.lower():
                            raw_text = teks
                            break
                        if not raw_text:
                            raw_text = teks
                    except asyncio.TimeoutError:
                        break
        except asyncio.TimeoutError:
            raw_text = "TIMEOUT"
        except errors.FloodWait as e:
            await asyncio.sleep(e.value)
            raise
        except Exception as e:
            raw_text = f"ERROR: {e}"

        if is_error_response(raw_text):
            return MissionResult(target=target, category="other", raw_text=raw_text)
        return parse_response(target, raw_text)