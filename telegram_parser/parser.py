import asyncio
import json
import os
import sys

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError


OPTIONS_FILE = "/data/options.json"
SESSION_FILE = "/data/telegram_parser"


def load_options():
    with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text):
    return " ".join(text.lower().split())


async def main():
    print("=" * 50, flush=True)
    print(" Telegram Channel Parser", flush=True)
    print("=" * 50, flush=True)

    options = load_options()

    api_id = int(options.get("api_id", 0))
    api_hash = options.get("api_hash", "")

    bot_token = options.get("bot_token", "")
    chat_id = int(options.get("chat_id", 0))

    channels = options.get("channels", [])
    keywords = options.get("keywords", [])

    if not api_id:
        print("ОШИБКА: api_id не указан", flush=True)
        sys.exit(1)

    if not api_hash:
        print("ОШИБКА: api_hash не указан", flush=True)
        sys.exit(1)

    if not channels:
        print("ОШИБКА: список channels пуст", flush=True)
        sys.exit(1)

    if not keywords:
        print("ОШИБКА: список keywords пуст", flush=True)
        sys.exit(1)

    print(f"API ID: {api_id}", flush=True)

    print()
    print("Каналы мониторинга:", flush=True)

    for channel in channels:
        print(f"  • {channel}", flush=True)

    print()
    print("Ключевые слова:", flush=True)

    for keyword in keywords:
        print(f"  • {keyword}", flush=True)

    print()

    client = TelegramClient(
        SESSION_FILE,
        api_id,
        api_hash,
    )

    await client.connect()

    if not await client.is_user_authorized():
        print("ОШИБКА: Telegram session не авторизована", flush=True)
        await client.disconnect()
        sys.exit(1)

    me = await client.get_me()

    print("=" * 50, flush=True)
    print(" TELEGRAM ПОДКЛЮЧЕН", flush=True)
    print("=" * 50, flush=True)

    print(
        f"Имя: {(me.first_name or '')} {(me.last_name or '')}",
        flush=True
    )

    if me.username:
        print(f"Username: @{me.username}", flush=True)

    print(f"ID: {me.id}", flush=True)

    print()
    print("Парсер запущен.", flush=True)
    print("Ожидаем новые сообщения...", flush=True)
    print("=" * 50, flush=True)

    # Приводим ключевые слова к нижнему регистру
    keywords_normalized = [
        normalize_text(keyword)
        for keyword in keywords
        if keyword.strip()
    ]

    # Приводим названия каналов к нормальному виду
    channel_entities = []

    for channel in channels:
        channel = channel.strip()

        if not channel:
            continue

        if channel.startswith("https://t.me/"):
            channel = channel.replace("https://t.me/", "")

        if channel.startswith("@"):
            channel = channel[1:]

        try:
            entity = await client.get_entity(channel)

            channel_entities.append(entity)

            print(
                f"✓ Канал подключен: @{channel}",
                flush=True
            )

        except Exception as e:
            print(
                f"✗ Не удалось подключить канал @{channel}: "
                f"{type(e).__name__}: {e}",
                flush=True
            )

    if not channel_entities:
        print()
        print("ОШИБКА: ни один канал не подключен.", flush=True)

        await client.disconnect()
        sys.exit(1)

    print()
    print(
        f"Мониторинг каналов: {len(channel_entities)}",
        flush=True
    )

    print(
        f"Ключевых слов: {len(keywords_normalized)}",
        flush=True
    )

    print()

    @client.on(events.NewMessage(chats=channel_entities))
    async def handler(event):

        text = event.raw_text or ""

        if not text.strip():
            return

        normalized_text = normalize_text(text)

        matched_keywords = []

        for keyword in keywords_normalized:
            if keyword in normalized_text:
                matched_keywords.append(keyword)

        if not matched_keywords:
            return

        try:
            chat = await event.get_chat()

            channel_title = getattr(
                chat,
                "title",
                None
            ) or getattr(
                chat,
                "username",
                "Неизвестный канал"
            )

        except Exception:
            channel_title = "Неизвестный канал"

        print()
        print("=" * 60, flush=True)
        print("🚨 НАЙДЕНО СОВПАДЕНИЕ", flush=True)
        print("=" * 60, flush=True)

        print(
            f"Канал: {channel_title}",
            flush=True
        )

        print(
            f"Совпадение: {', '.join(matched_keywords)}",
            flush=True
        )

        print()
        print("Сообщение:", flush=True)
        print(text, flush=True)

        print("=" * 60, flush=True)

        # Отправка через Telegram Bot
        if bot_token and chat_id:

            message = (
                f"🚨 <b>Найдено совпадение</b>\n\n"
                f"📢 <b>Канал:</b> {channel_title}\n"
                f"🔎 <b>Слово:</b> "
                f"{', '.join(matched_keywords)}\n\n"
                f"📝 <b>Сообщение:</b>\n"
                f"{text}"
            )

            try:
                await client.send_message(
                    chat_id,
                    message,
                    parse_mode="html",
                    bot_token=bot_token,
                )

                print(
                    "✓ Уведомление отправлено через Telegram Bot",
                    flush=True
                )

            except Exception as e:

                print(
                    "✗ Ошибка отправки уведомления: "
                    f"{type(e).__name__}: {e}",
                    flush=True
                )

        else:

            print(
                "⚠ bot_token или chat_id не настроены — "
                "уведомление не отправлено.",
                flush=True
            )

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
