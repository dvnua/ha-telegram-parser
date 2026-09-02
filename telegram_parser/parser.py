import asyncio
import html
import json
import sys
import urllib.parse
import urllib.request

from telethon import TelegramClient, events


OPTIONS_FILE = "/data/options.json"
SESSION_FILE = "/data/telegram_parser"


# ==========================================================
# Загрузка конфигурации Add-on
# ==========================================================

def load_options():

    with open(
        OPTIONS_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ==========================================================
# Нормализация текста для поиска
# ==========================================================

def normalize_text(text):

    return " ".join(
        text.lower().split()
    )


# ==========================================================
# Отправка сообщения через Telegram Bot API
# ==========================================================

async def send_telegram_message(
    bot_token,
    chat_id,
    message,
):

    url = (
        f"https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }
    ).encode("utf-8")

    def send():

        request = urllib.request.Request(
            url,
            data=data,
            method="POST",
        )

        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:

            return response.read()

    await asyncio.to_thread(send)


# ==========================================================
# Основная функция
# ==========================================================

async def main():

    print("=" * 60, flush=True)
    print(" Telegram Channel Parser", flush=True)
    print("=" * 60, flush=True)

    # ------------------------------------------------------
    # Загружаем настройки
    # ------------------------------------------------------

    options = load_options()

    api_id = int(
        options.get("api_id", 0)
    )

    api_hash = options.get(
        "api_hash",
        "",
    )

    bot_token = options.get(
        "bot_token",
        "",
    )

    chat_ids_raw = options.get(
        "chat_ids",
        "",
    )

    channels = options.get(
        "channels",
        [],
    )

    keywords = options.get(
        "keywords",
        [],
    )

    # ------------------------------------------------------
    # Преобразуем chat_ids из строки в список
    #
    # Формат:
    # 422025994,123456789,987654321
    # ------------------------------------------------------

    try:

        chat_ids = [
            int(chat_id.strip())
            for chat_id in chat_ids_raw.split(",")
            if chat_id.strip()
        ]

    except (AttributeError, TypeError, ValueError):

        print(
            "ОШИБКА: неверный формат chat_ids",
            flush=True,
        )

        print(
            "Используй формат:",
            flush=True,
        )

        print(
            "422025994,123456789",
            flush=True,
        )

        sys.exit(1)

    # ------------------------------------------------------
    # Проверка настроек
    # ------------------------------------------------------

    if not api_id:

        print(
            "ОШИБКА: api_id не указан",
            flush=True,
        )

        sys.exit(1)

    if not api_hash:

        print(
            "ОШИБКА: api_hash не указан",
            flush=True,
        )

        sys.exit(1)

    if not bot_token:

        print(
            "ОШИБКА: bot_token не указан",
            flush=True,
        )

        sys.exit(1)

    if not chat_ids:

        print(
            "ОШИБКА: список chat_ids пуст",
            flush=True,
        )

        sys.exit(1)

    if not channels:

        print(
            "ОШИБКА: список channels пуст",
            flush=True,
        )

        sys.exit(1)

    if not keywords:

        print(
            "ОШИБКА: список keywords пуст",
            flush=True,
        )

        sys.exit(1)

    # ------------------------------------------------------
    # Вывод конфигурации
    # ------------------------------------------------------

    print(
        f"API ID: {api_id}",
        flush=True,
    )

    print()

    print(
        "Каналы мониторинга:",
        flush=True,
    )

    for channel in channels:

        print(
            f"  • {channel}",
            flush=True,
        )

    print()

    print(
        "Ключевые слова:",
        flush=True,
    )

    for keyword in keywords:

        print(
            f"  • {keyword}",
            flush=True,
        )

    print()

    print(
        "Получатели уведомлений:",
        flush=True,
    )

    for chat_id in chat_ids:

        print(
            f"  • {chat_id}",
            flush=True,
        )

    print()

    # ------------------------------------------------------
    # Создаем Telegram Client
    # ------------------------------------------------------

    client = TelegramClient(
        SESSION_FILE,
        api_id,
        api_hash,
    )

    await client.connect()

    # ------------------------------------------------------
    # Проверка авторизации
    # ------------------------------------------------------

    if not await client.is_user_authorized():

        print(
            "ОШИБКА: Telegram session не авторизована",
            flush=True,
        )

        await client.disconnect()

        sys.exit(1)

    # ------------------------------------------------------
    # Информация об аккаунте
    # ------------------------------------------------------

    me = await client.get_me()

    print("=" * 60, flush=True)
    print(
        " TELEGRAM ПОДКЛЮЧЕН",
        flush=True,
    )
    print("=" * 60, flush=True)

    print(
        f"Имя: {(me.first_name or '')} "
        f"{(me.last_name or '')}",
        flush=True,
    )

    if me.username:

        print(
            f"Username: @{me.username}",
            flush=True,
        )

    print(
        f"ID: {me.id}",
        flush=True,
    )

    print()

    # ------------------------------------------------------
    # Подключение Telegram-каналов
    # ------------------------------------------------------

    channel_entities = []

    print(
        "Подключение каналов:",
        flush=True,
    )

    for channel in channels:

        channel = channel.strip()

        if not channel:

            continue

        # Поддержка ссылки t.me

        if channel.startswith(
            "https://t.me/"
        ):

            channel = channel.replace(
                "https://t.me/",
                "",
            )

        # Убираем @

        if channel.startswith("@"):

            channel = channel[1:]

        try:

            entity = await client.get_entity(
                channel
            )

            channel_entities.append(
                entity
            )

            title = getattr(
                entity,
                "title",
                None,
            )

            username = getattr(
                entity,
                "username",
                None,
            )

            if username:

                display_name = (
                    f"@{username}"
                )

            elif title:

                display_name = title

            else:

                display_name = channel

            print(
                f"✓ Канал подключен: "
                f"{display_name}",
                flush=True,
            )

        except Exception as e:

            print(
                f"✗ Не удалось подключить "
                f"{channel}: "
                f"{type(e).__name__}: {e}",
                flush=True,
            )

    # ------------------------------------------------------
    # Проверка подключенных каналов
    # ------------------------------------------------------

    if not channel_entities:

        print()

        print(
            "ОШИБКА: ни один канал "
            "не подключен.",
            flush=True,
        )

        await client.disconnect()

        sys.exit(1)

    # ======================================================
    # ОБРАБОТЧИК НОВЫХ СООБЩЕНИЙ
    # ======================================================

    @client.on(
        events.NewMessage(
            chats=channel_entities
        )
    )
    async def handler(event):

        text = event.raw_text or ""

        # Пропускаем пустые сообщения

        if not text.strip():

            return

        # Нормализуем текст

        normalized_text = normalize_text(
            text
        )

        matches = []

        # --------------------------------------------------
        # Поиск ключевых слов
        # --------------------------------------------------

        for keyword in keywords:

            keyword_normalized = (
                normalize_text(keyword)
            )

            if not keyword_normalized:

                continue

            if (
                keyword_normalized
                in normalized_text
            ):

                matches.append(
                    keyword
                )

        # Нет совпадений

        if not matches:

            return

        # --------------------------------------------------
        # Получаем информацию о канале
        # --------------------------------------------------

        try:

            chat = await event.get_chat()

            channel_title = (
                getattr(
                    chat,
                    "title",
                    None,
                )
                or getattr(
                    chat,
                    "username",
                    None,
                )
                or "Неизвестный канал"
            )

        except Exception:

            channel_title = (
                "Неизвестный канал"
            )

        # ==================================================
        # ЛОГ НАЙДЕННОГО СООБЩЕНИЯ
        # ==================================================

        print()

        print("=" * 60, flush=True)

        print(
            "🚨 НАЙДЕНО СОВПАДЕНИЕ",
            flush=True,
        )

        print("=" * 60, flush=True)

        print(
            f"Канал: {channel_title}",
            flush=True,
        )

        print()

        print(
            "Сработало:",
            flush=True,
        )

        for match in matches:

            print(
                f"• {match}",
                flush=True,
            )

        print()

        print(
            "Сообщение:",
            flush=True,
        )

        print(
            text,
            flush=True,
        )

        print("=" * 60, flush=True)

        # ==================================================
        # Формируем сообщение для Telegram
        # ==================================================

        safe_channel = html.escape(
            str(channel_title)
        )

        safe_matches = "\n".join(
            (
                f"• "
                f"{html.escape(str(match))}"
            )
            for match in matches
        )

        safe_text = html.escape(
            text
        )

        message = (
            "🚨 <b>НАЙДЕНО СОВПАДЕНИЕ</b>\n\n"
            f"📢 <b>Канал:</b> "
            f"{safe_channel}\n\n"
            f"🔎 <b>Сработало:</b>\n"
            f"{safe_matches}\n\n"
            f"📝 <b>Сообщение:</b>\n"
            f"{safe_text}"
        )

        # ==================================================
        # Отправляем сообщение всем получателям
        # ==================================================

        for chat_id in chat_ids:

            try:

                await send_telegram_message(
                    bot_token,
                    chat_id,
                    message,
                )

                print(
                    f"✓ Уведомление отправлено: "
                    f"{chat_id}",
                    flush=True,
                )

            except Exception as e:

                print(
                    f"✗ Ошибка отправки "
                    f"{chat_id}: "
                    f"{type(e).__name__}: {e}",
                    flush=True,
                )

    # ======================================================
    # ПАРСЕР ЗАПУЩЕН
    # ======================================================

    print()

    print("=" * 60, flush=True)

    print(
        " ПАРСЕР ЗАПУЩЕН",
        flush=True,
    )

    print("=" * 60, flush=True)

    print(
        f"Мониторинг каналов: "
        f"{len(channel_entities)}",
        flush=True,
    )

    print(
        f"Ключевых слов: "
        f"{len(keywords)}",
        flush=True,
    )

    print(
        f"Получателей: "
        f"{len(chat_ids)}",
        flush=True,
    )

    print()

    print(
        "Ожидаем новые сообщения...",
        flush=True,
    )

    print("=" * 60, flush=True)

    # ------------------------------------------------------
    # Бесконечная работа
    # ------------------------------------------------------

    await client.run_until_disconnected()


# ==========================================================
# Запуск
# ==========================================================

if __name__ == "__main__":

    asyncio.run(main())
