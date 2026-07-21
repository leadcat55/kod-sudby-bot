import json
from typing import List, Tuple, Optional
import requests

from .base import Channel, Incoming


class TelegramIncoming(Incoming):
    def __init__(self, bot, message: dict):
        self.bot = bot
        self.message = message
        self._text = message.get("text") or message.get("caption") or ""

    @property
    def text(self) -> str:
        return self._text

    def photo_bytes(self) -> Optional[bytes]:
        photos = self.message.get("photo")
        if not photos:
            return None
        file_id = photos[-1]["file_id"]
        info = self.bot.api("getFile", file_id=file_id)
        if not info.get("ok"):
            return None
        path = info["result"]["file_path"]
        url = f"https://api.telegram.org/file/bot{self.bot.token}/{path}"
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r.content
        except requests.RequestException:
            pass
        return None


class TelegramChannel(Channel):
    def __init__(self, bot, chat_id: int, incoming: TelegramIncoming):
        self.bot = bot
        self.chat_id = chat_id
        self._incoming = incoming

    @property
    def user_key(self) -> str:
        return f"tg:{self.chat_id}"

    @property
    def incoming(self) -> TelegramIncoming:
        return self._incoming

    def send_text(self, text: str) -> None:
        self.bot.api("sendMessage", chat_id=self.chat_id, text=text)

    def _reply_keyboard(self, options: List[Tuple[str, str]], per_row: int = 2):
        rows, row = [], []
        for _payload, label in options:
            row.append({"text": label})
            if len(row) == per_row:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        return json.dumps({
            "keyboard": rows,
            "resize_keyboard": True,
        })

    def send_buttons(self, text: str, options: List[Tuple[str, str]]) -> None:
        self.bot.api("sendMessage", chat_id=self.chat_id, text=text,
                     reply_markup=self._reply_keyboard(options))

    def send_start_keyboard(self) -> None:
        markup = json.dumps({
            "keyboard": [[{"text": "/start"}]],
            "resize_keyboard": True,
        })
        self.bot.api("sendMessage", chat_id=self.chat_id,
                     text="Нажмите /start чтобы начать",
                     reply_markup=markup)

    def send_photos(self, urls: List[str], caption: str) -> None:
        if len(urls) == 1:
            self.bot.api("sendPhoto", chat_id=self.chat_id,
                         photo=urls[0], caption=caption)
            return
        media = []
        for i, u in enumerate(urls):
            item = {"type": "photo", "media": u}
            if i == 0:
                item["caption"] = caption
            media.append(item)
        self.bot.api("sendMediaGroup", chat_id=self.chat_id,
                     media=json.dumps(media))
