import re
import hashlib
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MissionResult:
    target: str
    category: str
    raw_text: str
    missions: list[dict] = field(default_factory=list)
    identifier: Optional[str] = None

MISSION_LINE_PATTERN = re.compile(
    r"^[^\w]*"                           
    r"(?P<name>.+?)"                     
    r"\s*\((?P<coins>[\d.,]+)\s*koin\)"  
    r"\s*[—\-–]\s*"                      
    r"(?P<status>.+)$",                  
    re.IGNORECASE | re.UNICODE
)

def parse_response(target: str, raw_text: str) -> MissionResult:
    if not raw_text or not raw_text.strip():
        return MissionResult(target=target, category="other", raw_text=raw_text)

    missions = []
    for line in raw_text.splitlines():
        line = line.strip()
        m = MISSION_LINE_PATTERN.match(line)
        if m:
            missions.append({
                "name": m.group("name").strip(), 
                "coins": m.group("coins"), 
                "status": m.group("status").strip()
            })

    category = "coin" if missions else "other"
    fingerprint = hashlib.md5(f"{target}:{raw_text}".encode("utf-8", errors="replace")).hexdigest()

    return MissionResult(target=target, category=category, raw_text=raw_text, missions=missions, identifier=fingerprint)

def is_error_response(raw_text: str) -> bool:
    if not raw_text: return True
    error_keywords = ["timeout", "error", "gagal", "failed", "exception", "banned", "dibatasi"]
    return any(kw in raw_text.lower() for kw in error_keywords) and len(raw_text) < 200