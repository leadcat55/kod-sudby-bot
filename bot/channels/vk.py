import json
import time
from typing import List, Tuple, Optional
import requests

from .base import Channel, Incoming

VK_API_VERSION = "5.199"


class VkIncoming(Incoming):
    def __init__(self, bot, message: dict):
        self.bot = bot
        self.message = message
        self._text = message.get("text") or ""

    @property
    def text(self) -> str:
        return self._text

    def photo_bytes(self) -> Optional[bytes]:
        for att in self.message.get("attachments", []):
            if att.get("type") != "photo":
                continue
            sizes = att["photo"].get("sizes", [])
            if not sizes:
                continue
            best = max(sizes, key=lambda s: s.get("width", 0) * s.get("height", 0))
            try:
                r = requests.get(best["url"], timeout=60)
                if r.status_code == 200:
                    return r.content
            except requests.RequestException:
                pass
        return None


class VkChannel(Channel):
    def __init__(self, bot, peer_id: int, incoming: VkIncoming):
        self.bot = bot
        self.peer_id = peer_id
        self._incoming = incoming

    @property
    def user_key(self) -> str:
        return f"vk:{self.peer_id}"

    @property
    def incoming(self) -> VkIncoming:
        return self._incoming

    def send_text(self, text: str) -> None:
        self.bot.send_message(self.peer_id, text)

    def _keyboard(self, options: List[Tuple[str, str]], per_row: int = 2):
        rows, row = [], []
        for payload, label in options:
            row.append({
                "action": {
                    "type": "text",
                    "label": label[:40],
                    "payload": json.dumps({"p": payload}),
                },
                "color": "primary",
            })
            if len(row) == per_row:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return json.dumps({"one_time": True, "buttons": rows}, ensure_ascii=False)

    def send_buttons(self, text: str, options: List[Tuple[str, str]]) -> None:
        self.bot.send_message(self.peer_id, text,
                              keyboard=self._keyboard(options))

    def send_photos(self, urls: List[str], caption: str) -> None:
        attachments = []
        for u in urls:
            try:
                r = requests.get(u, timeout=60)
                if r.status_code == 200:
                    att = self.bot.upload_photo(self.peer_id, r.content)
                    if att:
                        attachments.append(att)
            except requests.RequestException:
                pass
        self.bot.send_message(self.peer_id, caption,
                              attachment=",".join(attachments) or None)