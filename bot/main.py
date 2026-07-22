import asyncio
import logging
import os
import sys
import threading
import time
import traceback

import requests

from .config import config
from .services.database import db
from .services.payments import payments
from .channels.telegram import TelegramChannel, TelegramIncoming
from .channels.vk import VkChannel, VkIncoming
from .channels.max import MaxChannel, MaxIncoming
from . import dialog

# Load tokens from config
TELEGRAM_TOKEN = config.BOT_TOKEN or ""
VK_TOKEN = os.environ.get("VK_TOKEN", "").strip()
VK_GROUP_ID = os.environ.get("VK_GROUP_ID", "").strip()
MAX_TOKEN = os.environ.get("MAX_TOKEN", "").strip()

HTTP_TIMEOUT = 100


def log(platform: str, message: str) -> None:
    print(f"[{platform}] {message}", flush=True)


# ===========================================================================
# Telegram Bot
# ===========================================================================

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base = f"https://api.telegram.org/bot{token}"
        self.session = requests.Session()

    def api(self, method: str, **params) -> dict:
        r = self.session.post(f"{self.base}/{method}", data=params,
                              timeout=HTTP_TIMEOUT)
        return r.json()

    def run(self):
        log("Telegram", "запущен")
        offset = None
        while True:
            try:
                params = {"timeout": 60, "allowed_updates": '["message"]'}
                if offset is not None:
                    params["offset"] = offset
                data = self.session.get(f"{self.base}/getUpdates",
                                        params=params, timeout=HTTP_TIMEOUT).json()
                if not data.get("ok"):
                    log("Telegram", f"ошибка API: {data}")
                    time.sleep(3)
                    continue
                for upd in data["result"]:
                    offset = upd["update_id"] + 1
                    msg = upd.get("message")
                    if not msg:
                        continue
                    chat_id = msg["chat"]["id"]
                    incoming = TelegramIncoming(self, msg)
                    channel = TelegramChannel(self, chat_id, incoming)
                    try:
                        dialog.handle(channel.user_key, channel)
                    except Exception:
                        log("Telegram", f"ошибка: {traceback.format_exc()}")
            except requests.RequestException as e:
                log("Telegram", f"сетевая ошибка: {e}")
                time.sleep(3)


# ===========================================================================
# VK Bot
# ===========================================================================

VK_API_VERSION = "5.199"


class VkBot:
    def __init__(self, token: str, group_id: str):
        self.token = token
        self.group_id = "".join(filter(str.isdigit, group_id))
        self.session = requests.Session()
        self._rand = int(time.time())

    def api(self, method: str, **params) -> dict:
        params.update({"access_token": self.token, "v": VK_API_VERSION})
        r = self.session.post(f"https://api.vk.com/method/{method}",
                              data=params, timeout=HTTP_TIMEOUT)
        return r.json()

    def send_message(self, peer_id: int, text: str, attachment=None, keyboard=None):
        self._rand += 1
        params = {"peer_id": peer_id, "random_id": self._rand}
        if text:
            params["message"] = text
        if attachment:
            params["attachment"] = attachment
        if keyboard:
            params["keyboard"] = keyboard
        self.api("messages.send", **params)

    def upload_photo(self, peer_id: int, image_bytes: bytes):
        srv = self.api("photos.getMessagesUploadServer", peer_id=peer_id)
        if "error" in srv:
            return None
        upload_url = srv["response"]["upload_url"]
        try:
            up = self.session.post(
                upload_url,
                files={"photo": ("photo.jpg", image_bytes, "image/jpeg")},
                timeout=HTTP_TIMEOUT,
            ).json()
        except requests.RequestException:
            return None
        saved = self.api("photos.saveMessagesPhoto",
                         photo=up.get("photo"), server=up.get("server"),
                         hash=up.get("hash"))
        if "error" in saved or not saved.get("response"):
            return None
        p = saved["response"][0]
        return f"photo{p['owner_id']}_{p['id']}"

    def run(self):
        if not self.group_id:
            log("VK", "не указан VK_GROUP_ID — пропущен")
            return
        log("VK", "запущен")
        while True:
            try:
                srv = self.api("groups.getLongPollServer", group_id=self.group_id)
                if "error" in srv:
                    log("VK", f"ошибка: {srv['error']}")
                    time.sleep(5)
                    continue
                server = srv["response"]["server"]
                key = srv["response"]["key"]
                ts = srv["response"]["ts"]
                while True:
                    r = self.session.get(
                        server,
                        params={"act": "a_check", "key": key, "ts": ts, "wait": 25},
                        timeout=HTTP_TIMEOUT,
                    ).json()
                    if "failed" in r:
                        break
                    ts = r["ts"]
                    for event in r.get("updates", []):
                        if event.get("type") != "message_new":
                            continue
                        msg = event["object"]["message"]
                        peer_id = msg["peer_id"]
                        incoming = VkIncoming(self, msg)
                        channel = VkChannel(self, peer_id, incoming)
                        try:
                            dialog.handle(channel.user_key, channel)
                        except Exception:
                            log("VK", f"ошибка: {traceback.format_exc()}")
            except requests.RequestException as e:
                log("VK", f"сетевая ошибка: {e}")
                time.sleep(5)


# ===========================================================================
# MAX Bot
# ===========================================================================

class MaxBot:
    def __init__(self, token: str):
        self.token = token
        self.base = "https://platform-api.max.ru"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": token})

    def send(self, params: dict, body: dict):
        try:
            self.session.post(f"{self.base}/messages", params=params,
                              json=body, timeout=HTTP_TIMEOUT)
        except requests.RequestException as e:
            log("MAX", f"send: {e}")

    def upload_image(self, image_bytes: bytes):
        try:
            up = self.session.post(f"{self.base}/uploads",
                                   params={"type": "image"},
                                   timeout=HTTP_TIMEOUT).json()
            upload_url = up.get("url")
            if not upload_url:
                return None
            res = self.session.post(
                upload_url,
                files={"data": ("photo.jpg", image_bytes, "image/jpeg")},
                timeout=HTTP_TIMEOUT,
            ).json()
            if "token" in res:
                return res["token"]
            photos = res.get("photos") or {}
            for v in photos.values():
                if isinstance(v, dict) and v.get("token"):
                    return v["token"]
            return None
        except requests.RequestException:
            return None

    def run(self):
        log("MAX", "запущен")
        marker = None
        while True:
            try:
                params = {"timeout": 90,
                          "types": "message_created,message_callback"}
                if marker is not None:
                    params["marker"] = marker
                data = self.session.get(f"{self.base}/updates", params=params,
                                        timeout=HTTP_TIMEOUT).json()
                marker = data.get("marker", marker)
                for upd in data.get("updates", []):
                    utype = upd.get("update_type")
                    if utype == "message_created":
                        message = upd.get("message", {})
                        recipient = message.get("recipient", {})
                        chat_id = recipient.get("chat_id")
                        user_id = recipient.get("user_id")
                        incoming = MaxIncoming(self, message)
                        channel = MaxChannel(self, chat_id, user_id, incoming)
                        try:
                            dialog.handle(channel.user_key, channel)
                        except Exception:
                            log("MAX", f"ошибка: {traceback.format_exc()}")
            except requests.RequestException as e:
                log("MAX", f"сетевая ошибка: {e}")
                time.sleep(3)


# ===========================================================================
# Payment Poller
# ===========================================================================

def payment_poller():
    """Background YooKassa payment status checker"""
    log("payments", "поллер запущен")
    while True:
        try:
            # Get pending payments from database
            import asyncio
            pending = asyncio.run(db.get_pending_payments())

            for payment in pending:
                payment_id = payment["payment_id"]
                try:
                    status = payments.get_status(payment_id)
                    if status == "succeeded":
                        # Payment completed - update user
                        user_key = payment["user_key"]
                        plan_id = payment["plan_id"]
                        asyncio.run(_complete_payment(user_key, plan_id))
                        asyncio.run(db.update_payment_status(payment_id, "succeeded"))
                        log("payments", f"Платёж {payment_id} успешно завершён")
                    elif status == "canceled":
                        asyncio.run(db.update_payment_status(payment_id, "canceled"))
                        log("payments", f"Платёж {payment_id} отменён")
                except Exception as e:
                    log("payments", f"Ошибка проверки {payment_id}: {e}")
        except Exception as e:
            log("payments", f"ошибка: {e}")
        time.sleep(30)


async def _complete_payment(user_key: str, plan_id: str) -> None:
    """Complete payment and update user subscription"""
    from datetime import datetime, timedelta
    from .services.database import db

    platform, user_id = user_key.split(":")
    user_id = int(user_id)

    user = await db.get_user(user_id)
    if not user:
        return

    if plan_id == "subscription":
        user.subscription_status = "premium"
        user.subscription_expires = datetime.now() + timedelta(days=365)
    elif plan_id in ("basic", "full"):
        user.premium_reports_count += 1

    await db.update_user(user)


# ===========================================================================
# Main
# ===========================================================================

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    await db.init_db()
    
    # Check payments configuration
    if payments.is_configured():
        log("main", "ЮKassa настроена — приём оплаты включён")
        threading.Thread(target=payment_poller, name="payments", daemon=True).start()
    else:
        log("main", "ВНИМАНИЕ: ключи ЮKassa не заданы — оплата недоступна")
    
    # Start platforms
    platforms = []
    if TELEGRAM_TOKEN:
        platforms.append(("Telegram", TelegramBot(TELEGRAM_TOKEN).run))
    if VK_TOKEN:
        platforms.append(("VK", VkBot(VK_TOKEN, VK_GROUP_ID).run))
    if MAX_TOKEN:
        platforms.append(("MAX", MaxBot(MAX_TOKEN).run))
    
    if not platforms:
        sys.exit("Не задан ни один токен в .env")
    
    log("main", f"Запускаю платформы: {', '.join(n for n, _ in platforms)}")
    
    # Run platforms in threads
    for name, target in platforms:
        threading.Thread(target=target, name=name, daemon=True).start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        log("main", "Остановка по Ctrl+C")


if __name__ == "__main__":
    asyncio.run(main())
