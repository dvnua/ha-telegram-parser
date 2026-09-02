import asyncio
import json
import os
import sys

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

OPTIONS_FILE = "/data/options.json"
SESSION_FILE = "/data/telegram_parser"

PHONE_FILE = "/share/telegram_phone.txt"
CODE_FILE = "/share/telegram_code.txt"
PASSWORD_FILE = "/share/telegram_2fa.txt"


def load_options():
    with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def read_file(path):
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        value = f.read().strip()

    return value if value else None


def delete_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Не удалось удалить {path}: {e}")


async def authorize(client, phone):
    print("=" * 50)
    print(" ТРЕБУЕТСЯ АВТОРИЗАЦИЯ TELEGRAM")
    print("=" * 50)
    print(f"Телефон: {phone}")
    print()

    await client.send_code_request(phone)

    print("Код подтверждения отправлен в Telegram.")
    print()
    print(f"Ожидаем код в файле:")
    print(CODE_FILE)
    print()

    while True:
        code = read_file(CODE_FILE)

        if code:
            delete_file(CODE_FILE)
            break

        await asyncio.sleep(2)

    print("Код получен.")

    try:
        await client.sign_in(
            phone=phone,
            code=code
        )

    except SessionPasswordNeededError:
        print()
        print("Требуется пароль двухфакторной авторизации.")
        print(f"Ожидаем пароль в файле:")
        print(PASSWORD_FILE)
        print()

        while True:
            password = read_file(PASSWORD_FILE)

            if password:
                delete_file(PASSWORD_FILE)
                break

            await asyncio.sleep(2)

        await client.sign_in(password=password)

    print()
    print("=" * 50)
    print(" TELEGRAM УСПЕШНО АВТОРИЗОВАН")
    print("=" * 50)


async def main():
    print("=" * 50)
    print(" Telegram Channel Parser")
    print("=" * 50)

    options = load_options()

    api_id = int(options.get("api_id", 0))
    api_hash = options.get("api_hash", "")

    if not api_id:
        print("ОШИБКА: api_id не указан")
        sys.exit(1)

    if not api_hash:
        print("ОШИБКА: api_hash не указан")
        sys.exit(1)

    print(f"API ID: {api_id}")

    client = TelegramClient(
        SESSION_FILE,
        api_id,
        api_hash
    )

    await client.connect()

    if not await client.is_user_authorized():
        print()
        print("Telegram session отсутствует.")
        print()

        phone = read_file(PHONE_FILE)

        if not phone:
            print("=" * 50)
            print("ОШИБКА: не найден номер телефона")
            print("=" * 50)
            print()
            print(f"Создай файл:")
            print(PHONE_FILE)
            print()
            print("В файл запиши номер телефона")
            print("в международном формате.")
            print()
            await client.disconnect()
            sys.exit(1)

        await authorize(client, phone)

        delete_file(PHONE_FILE)

    me = await client.get_me()

    print()
    print("=" * 50)
    print(" TELEGRAM ПОДКЛЮЧЕН")
    print("=" * 50)

    print(f"Имя: {me.first_name or ''} {me.last_name or ''}")

    if me.username:
        print(f"Username: @{me.username}")

    print(f"ID: {me.id}")
    print()
    print("Session сохранена.")
    print("Повторная авторизация больше не потребуется.")
    print("=" * 50)

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
