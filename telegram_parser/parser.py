import asyncio
import json
import os
import sys

from telethon import TelegramClient
from telethon.errors import (
    AuthRestartError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError,
)

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

    try:
        with open(path, "r", encoding="utf-8") as f:
            value = f.read().strip()
    except Exception:
        return None

    return value if value else None


def delete_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Не удалось удалить {path}: {e}")


async def request_code(client, phone):
    """
    Запрашивает код Telegram.
    При AuthRestartError повторяет запрос.
    """

    for attempt in range(1, 6):
        try:
            print()
            print(f"Запрашиваем код Telegram... попытка {attempt}/5")

            result = await asyncio.wait_for(
                client.send_code_request(phone),
                timeout=60
            )

            print()
            print("Код подтверждения отправлен в Telegram.")
            print()
            print("Ожидаем код в файле:")
            print(CODE_FILE)
            print()

            return result

        except AuthRestartError:
            print()
            print("Telegram потребовал перезапустить авторизацию.")
            print("Повторяем запрос нового кода...")
            print()

            await asyncio.sleep(3)

        except Exception as e:
            print()
            print(f"Ошибка при запросе кода: {type(e).__name__}: {e}")
            print("Повторяем через 5 секунд...")
            print()

            await asyncio.sleep(5)

    print()
    print("=" * 50)
    print("ОШИБКА: не удалось получить код Telegram")
    print("=" * 50)

    await client.disconnect()
    sys.exit(1)


async def wait_for_code():
    print("Ожидаем код...")

    while True:
        code = read_file(CODE_FILE)

        if code:
            delete_file(CODE_FILE)
            print("Код получен.")
            return code

        await asyncio.sleep(2)


async def wait_for_password():
    print()
    print("=" * 50)
    print("ТРЕБУЕТСЯ ПАРОЛЬ 2FA")
    print("=" * 50)
    print()
    print("Ожидаем пароль в файле:")
    print(PASSWORD_FILE)
    print()

    while True:
        password = read_file(PASSWORD_FILE)

        if password:
            delete_file(PASSWORD_FILE)
            return password

        await asyncio.sleep(2)


async def authorize(client, phone):
    print()
    print("=" * 50)
    print(" ТРЕБУЕТСЯ АВТОРИЗАЦИЯ TELEGRAM")
    print("=" * 50)
    print(f"Телефон: {phone}")
    print()

    # Удаляем старый код, если он случайно остался
    delete_file(CODE_FILE)

    code_request = await request_code(client, phone)

    code = await wait_for_code()

    try:
        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=code_request.phone_code_hash,
        )

    except SessionPasswordNeededError:
        password = await wait_for_password()

        await client.sign_in(password=password)

    except PhoneCodeInvalidError:
        print()
        print("=" * 50)
        print("ОШИБКА: код Telegram недействителен")
        print("=" * 50)
        print()
        print("Запусти Add-on заново и используй самый последний код.")
        print()

        await client.disconnect()
        sys.exit(1)

    except PhoneCodeExpiredError:
        print()
        print("=" * 50)
        print("ОШИБКА: код Telegram истёк")
        print("=" * 50)
        print()
        print("Запусти Add-on заново и запроси новый код.")
        print()

        await client.disconnect()
        sys.exit(1)

    print()
    print("=" * 50)
    print(" TELEGRAM УСПЕШНО АВТОРИЗОВАН")
    print("=" * 50)
    print()

    delete_file(PHONE_FILE)


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
        api_hash,
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print()
            print("Telegram session отсутствует.")

            phone = read_file(PHONE_FILE)

            if not phone:
                print()
                print("=" * 50)
                print("ОШИБКА: не найден номер телефона")
                print("=" * 50)
                print()
                print(f"Создай файл:")
                print(PHONE_FILE)
                print()

                await client.disconnect()
                sys.exit(1)

            await authorize(client, phone)

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

    except Exception as e:
        print()
        print("=" * 50)
        print("КРИТИЧЕСКАЯ ОШИБКА")
        print("=" * 50)
        print(f"{type(e).__name__}: {e}")
        print("=" * 50)
        print()

        try:
            await client.disconnect()
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
