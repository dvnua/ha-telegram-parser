import asyncio
import json
import os

from telethon import TelegramClient


OPTIONS_FILE = "/data/options.json"
SESSION_FILE = "/data/telegram_parser"


def load_options():
    with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


async def main():
    print("=" * 50)
    print(" Telegram Channel Parser")
    print("=" * 50)

    options = load_options()

    api_id = int(options.get("api_id", 0))
    api_hash = options.get("api_hash", "")

    if not api_id:
        print("ОШИБКА: api_id не указан")
        return

    if not api_hash:
        print("ОШИБКА: api_hash не указан")
        return

    print(f"API ID: {api_id}")
    print("Запуск Telegram Client...")
    print()
    print("При первом запуске Telegram может запросить:")
    print("1. Номер телефона")
    print("2. Код подтверждения")
    print("3. Пароль 2FA")
    print()

    client = TelegramClient(
        SESSION_FILE,
        api_id,
        api_hash
    )

    await client.start()

    me = await client.get_me()

    print("=" * 50)
    print(" TELEGRAM АВТОРИЗОВАН")
    print("=" * 50)
    print(f"Имя: {me.first_name or ''} {me.last_name or ''}")

    if me.username:
        print(f"Username: @{me.username}")

    print(f"ID: {me.id}")
    print()
    print("Session сохранена.")
    print("Повторная авторизация при перезапуске не потребуется.")
    print("=" * 50)

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
