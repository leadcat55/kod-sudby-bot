import json
from typing import List, Tuple, Optional
import requests

from .base import Channel, Incoming


class MaxIncoming(Incoming):
    def __init__(self, bot, message: dict):
        self.bot = bot
        self.message = message
        body = message.get("body", {})
        self._text = body.get("text") or ""

    @property
    def text(self) -> str:
        return self._text

    def photo_bytes(self) -> Optional[bytes]:
        body = self.message.get("body", {})
        for att in body.get("attachments", []):
            if att.get("type") != "image":
                continue
            payload = att.get("payload", {})
            url = payload.get("url") or payload.get("token")
            if url and url.startswith("http"):
                try:
                    r = requests.get(url, timeout=60)
                    if r.status_code == 200:
                        return r.content
                except requests.RequestException:
                    pass
        return None


class MaxChannel(Channel):
    def __init__(self, bot, chat_id, user_id, incoming: MaxIncoming):
        self.bot = bot
        self.chat_id = chat_id
        self.user_id = user_id
        self._incoming = incoming

    @property
    def user_key(self) -> str:
        if self.chat_id is not None:
            return f"max:c{self.chat_id}"
        return f"max:u{self.user_id}"

    @property
    def incoming(self) -> MaxIncoming:
        return self._incoming

    def _send_params(self):
        if self.chat_id is not None:
            return {"chat_id": self.chat_id}
        return {"user_id": self.user_id}

    def send_text(self, text: str) -> None:
        self.bot.send(self._send_params(), {"text": text})

    def _keyboard_attachment(self, options: List[Tuple[str, str]], per_row: int = 2):
        rows, row = [], []
        for payload, label in options:
            row.append({"type": "callback", "text": label[:40],
                        "payload": payload})
            if len(row) == per_row:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return {"type": "inline_keyboard", "payload": {"buttons": rows}}

    def send_buttons(self, text: str, options: List[Tuple[str, str]]) -> None:
        self.bot.send(self._send_params(), {
            "text": text,
            "attachments": [self._keyboard_attachment(options)],
        })

    def send_photos(self, urls: List[str], caption: str) -> None:
        tokens = []
        for u in urls:
            try:
                r = requests.get(u, timeout=60)
                if r.status_code == 200:
                    tok = self.bot.upload_image(r.content)
                    if tok:
                        tokens.append(tok)
            except requests.RequestException:
                pass
        if not tokens:
            self.send_text(caption + "\n(не удалось приложить изображения)")
            return
        attachments = [{"type": "image", "payload": {"token": t}} for t in tokens]
        self.bot.send(self._send_params(),
                      {"text": caption, "attachments": attachments})