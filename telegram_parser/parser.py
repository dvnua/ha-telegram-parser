import asyncio
import html
import json
import sys

from telethon import TelegramClient, events


OPTIONS_FILE = "/data/options.json"
SESSION_FILE = "/data/telegram_parser"


def load_options():
    with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text):
    """
    Приводит текст к нижнему регистру
    и убирает лишние пробелы.
    """
    return " ".join(text.lower().split())


def normalize_keyword(keyword):
    return normalize_text(keyword)


def parse_combinations(combinations):
    """
    Преобразует:

    "реактиви + Київ"
    "ракета + Київ + пуск"

    в:

    [
        ["реактиви", "київ"],
        ["ракета", "київ", "пуск"]
    ]
    """

    result = []

    for combination in combinations:

        if not combination:
            continue

        parts = combination.split("+")

        words = []

        for part in parts:
            part = normalize_keyword(part)

            if part:
                words.append(part)

        if words:
            result.append(words)

    return result


def find_matches(text, keywords, combinations):
    """
    Проверяет ОДНО конкретное сообщение.

    Возвращает список сработавших условий.
    """

    normalized_text = normalize_text(text)

    matches = []

    # ---------------------------------------------------------
    # Одиночные ключевые слова
    # ---------------------------------------------------------

    for keyword in keywords:

        keyword_normalized = normalize_keyword(keyword)

        if not keyword_normalized:
            continue

        if keyword_normalized in normalized_text:

            matches.append(
                {
                    "type": "keyword",
                    "condition": keyword,
                }
            )

    # ---------------------------------------------------------
    # Комбинации
    #
    # ВСЕ слова должны присутствовать
    # В ЭТОМ ЖЕ СООБЩЕНИИ.
    # ---------------------------------------------------------

    for combination in combinations:

        if not combination:
            continue

        if all(
            word in normalized_text
            for word in combination
        ):

            matches.append(
                {
                    "type": "combination",
                    "condition": " + ".join(combination),
                }
            )

    return matches


async def main():

    print("=" * 60, flush=True)
    print(" Telegram Channel Parser", flush=True)
    print("=" * 60, flush=True)

    options = load_options()

    api_id = int(options.get("api_id", 0))
    api_hash = options.get("api_hash", "")

    bot_token = options.get("bot_token", "")
    chat_id = int(options.get("chat_id", 0))

    channels = options.get("channels", [])
    keywords = options.get("keywords", [])
    combinations_raw = options.get("combinations", [])

    # ---------------------------------------------------------
    # Проверка настроек
    # ---------------------------------------------------------

    if not api_id:
        print("ОШИБКА: api_id не указан", flush=True)
        sys.exit(1)

    if not api_hash:
        print("ОШИБКА: api_hash не указан", flush=True)
        sys.exit(1)

    if not channels:
        print("ОШИБКА: список channels пуст", flush=True)
        sys.exit(1)

    if not keywords and not combinations_raw:
        print(
            "ОШИБКА: не указаны keywords или combinations",
            flush=True,
        )
        sys.exit(1)

    # ---------------------------------------------------------
    # Разбираем комбинации
    # ---------------------------------------------------------

    combinations = parse_combinations(
        combinations_raw
    )

    # ---------------------------------------------------------
    # Вывод конфигурации
    # ---------------------------------------------------------

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
        "Одиночные ключевые слова:",
        flush=True,
    )

    if keywords:

        for keyword in keywords:
            print(
                f"  • {keyword}",
                flush=True,
            )

    else:
        print(
            "  • нет",
            flush=True,
        )

    print()
    print(
        "Комбинации:",
        flush=True,
    )

    if combinations:

        for combination in combinations:
            print(
                f"  • {' + '.join(combination)}",
                flush=True,
            )

    else:
        print(
            "  • нет",
            flush=True,
        )

    print()

    # ---------------------------------------------------------
    # Telegram Client
    # ---------------------------------------------------------

    client = TelegramClient(
        SESSION_FILE,
        api_id,
        api_hash,
    )

    await client.connect()

    if not await client.is_user_authorized():

        print(
            "ОШИБКА: Telegram session не авторизована",
            flush=True,
        )

        await client.disconnect()
        sys.exit(1)

    me = await client.get_me()

    print("=" * 60, flush=True)
    print(" TELEGRAM ПОДКЛЮЧЕН", flush=True)
    print("=" * 60, flush=True)

    print(
        f"Имя: {(me.first_name or '')} {(me.last_name or '')}",
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

    # ---------------------------------------------------------
    # Подключаем каналы
    # ---------------------------------------------------------

    channel_entities = []

    print(
        "Подключение каналов:",
        flush=True,
    )

    for channel in channels:

        channel = channel.strip()

        if not channel:
            continue

        if channel.startswith("https://t.me/"):

            channel = channel.replace(
                "https://t.me/",
                "",
            )

        if channel.startswith("@"):

            channel = channel[1:]

        try:

            entity = await client.get_entity(
                channel
            )

            channel_entities.append(entity)

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

                display_name = f"@{username}"

            elif title:

                display_name = title

            else:

                display_name = channel

            print(
                f"✓ Канал подключен: {display_name}",
                flush=True,
            )

        except Exception as e:

            print(
                f"✗ Не удалось подключить "
                f"{channel}: "
                f"{type(e).__name__}: {e}",
                flush=True,
            )

    if not channel_entities:

        print()
        print(
            "ОШИБКА: ни один канал не подключен.",
            flush=True,
        )

        await client.disconnect()
        sys.exit(1)

    # ---------------------------------------------------------
    # Обработчик новых сообщений
    # ---------------------------------------------------------

    @client.on(
        events.NewMessage(
            chats=channel_entities
        )
    )
    async def handler(event):

        text = event.raw_text or ""

        if not text.strip():
            return

        # -----------------------------------------------------
        # Ищем совпадения ТОЛЬКО в текущем сообщении
        # -----------------------------------------------------

        matches = find_matches(
            text,
            keywords,
            combinations,
        )

        if not matches:
            return

        # -----------------------------------------------------
        # Получаем информацию о канале
        # -----------------------------------------------------

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

            channel_title = "Неизвестный канал"

        # -----------------------------------------------------
        # Формируем список условий
        # -----------------------------------------------------

        conditions = []

        for match in matches:

            if match["type"] == "keyword":

                conditions.append(
                    f"слово: {match['condition']}"
                )

            elif match["type"] == "combination":

                conditions.append(
                    f"комбинация: {match['condition']}"
                )

        conditions_text = "\n".join(
            f"• {condition}"
            for condition in conditions
        )

        # -----------------------------------------------------
        # ЛОГ
        # -----------------------------------------------------

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

        print(
            "Сработало:",
            flush=True,
        )

        print(
            conditions_text,
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

        # -----------------------------------------------------
        # Отправка через Telegram Bot
        # -----------------------------------------------------

        if bot_token and chat_id:

            safe_channel = html.escape(
                str(channel_title)
            )

            safe_conditions = html.escape(
                conditions_text
            )

            safe_text = html.escape(
                text
            )

            message = (
                "🚨 <b>НАЙДЕНО СОВПАДЕНИЕ</b>\n\n"
                f"📢 <b>Канал:</b> "
                f"{safe_channel}\n\n"
                f"🔎 <b>Сработало:</b>\n"
                f"{safe_conditions}\n\n"
                f"📝 <b>Сообщение:</b>\n"
                f"{safe_text}"
            )

            try:

                await client.send_message(
                    chat_id,
                    message,
                    parse_mode="html",
                    bot_token=bot_token,
                )

                print(
                    "✓ Уведомление отправлено "
                    "через Telegram Bot",
                    flush=True,
                )

            except Exception as e:

                print(
                    "✗ Ошибка отправки уведомления: "
                    f"{type(e).__name__}: {e}",
                    flush=True,
                )

        else:

            print(
                "⚠ bot_token или chat_id не настроены.",
                flush=True,
            )

    # ---------------------------------------------------------
    # ГОТОВО
    # ---------------------------------------------------------

    print()
    print("=" * 60, flush=True)
    print(
        " ПАРСЕР ЗАПУЩЕН",
        flush=True,
    )
    print("=" * 60, flush=True)

    print(
        f"Мониторинг каналов: {len(channel_entities)}",
        flush=True,
    )

    print(
        f"Одиночных слов: {len(keywords)}",
        flush=True,
    )

    print(
        f"Комбинаций: {len(combinations)}",
        flush=True,
    )

    print()
    print(
        "Ожидаем новые сообщения...",
        flush=True,
    )

    print("=" * 60, flush=True)

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
