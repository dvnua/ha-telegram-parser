import os
import asyncio
from telethon import TelegramClient

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")

SESSION_FILE = "/data/telegram_parser"

async def main():
    print("========================================")
    print(" Telegram Channel Parser")
    print("========================================")

    if not API_ID or not API_HASH:
        print("ОШИБКА: API_ID или API_HASH не указаны")
        return

    print(f"API ID: {API_ID}")
    print("Запускаем Telegram Client...")

    client = TelegramClient(
        SESSION_FILE,
        API_ID,
        API_HASH
    )

    await client.start()

    me = await client.get_me()

    print("----------------------------------------")
    print("Telegram авторизован!")
    print(f"Аккаунт: {me.first_name} {me.last_name or ''}")
    print(f"Username: @{me.username}" if me.username else "Username: отсутствует")
    print("----------------------------------------")

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
