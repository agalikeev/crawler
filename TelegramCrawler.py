import asyncio
from telethon import TelegramClient
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

# Настройка
load_dotenv()
plt.switch_backend('agg')


def search_in_university_channels():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_name = "university_search"

    # Расширенный список каналов
    university_channels = [
        'nakedboots',  # Официальный канал СПбГУ
    ]

    # Расширенный список ключевых слов с разными формами
    keywords = [
        "вариант"
    ]

    stats = {
        'post_count': 0,
        'unique_channels': set(),
        'daily_posts': defaultdict(int),
        'errors': [],
        'found_messages': []
    }

    with TelegramClient(session_name, api_id, api_hash) as client:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # Увеличили период до 6 месяцев

        for channel in university_channels:
            try:
                print(f"\n🔍 Анализирую канал: {channel}...")

                try:
                    entity = client.get_entity(channel)
                except ValueError as e:
                    print(f"⚠️ Канал {channel} не найден или недоступен: {str(e)}")
                    stats['errors'].append(f"Канал {channel} не найден")
                    continue

                # Ищем без параметра search, который может работать некорректно
                for message in client.iter_messages(
                        entity,
                        offset_date=end_date,
                        reverse=True,
                        limit=1000  # Ограничиваем количество сообщений для анализа
                ):
                    if message.date < start_date:
                        break

                    if not hasattr(message, 'text') or not message.text:
                        continue

                    text = message.text.lower()
                    if any(keyword.lower() in text for keyword in keywords):
                        post_date = message.date.strftime('%Y-%m-%d')
                        stats['daily_posts'][post_date] += 1
                        stats['post_count'] += 1
                        stats['unique_channels'].add(channel)
                        stats['found_messages'].append({
                            'date': post_date,
                            'text': message.text[:100] + '...' if len(message.text) > 100 else message.text,
                            'channel': channel
                        })
                        print(f"✅ Найдено сообщение от {post_date}")

            except Exception as e:
                error_msg = f"⛔ Ошибка в канале {channel}: {str(e)}"
                stats['errors'].append(error_msg)
                print(error_msg)
                continue

        stats['unique_channels'] = len(stats['unique_channels'])
        return stats


def main():
    print("🚀 Начинаю поиск упоминаний университетов...")
    stats = search_in_university_channels()

    print("\n📊 Результаты поиска:")
    print(f"• Всего публикаций: {stats['post_count']}")
    print(f"• Уникальных каналов: {stats['unique_channels']}")

    if stats['errors']:
        print("\n❌ Ошибки при работе:")
        for error in stats['errors']:
            print(f"- {error}")

    if stats['found_messages']:
        print("\n🔎 Найденные сообщения (первые 5):")
        for msg in stats['found_messages'][:5]:
            print(f"\n📅 {msg['date']} | 📢 {msg['channel']}")
            print(f"📝 {msg['text']}")

    if stats['daily_posts']:
        dates = sorted(stats['daily_posts'].keys())
        counts = [stats['daily_posts'][date] for date in dates]

        plt.figure(figsize=(12, 6))
        plt.bar(dates, counts)
        plt.title('Динамика упоминаний университетской тематики')
        plt.xlabel('Дата')
        plt.ylabel('Количество сообщений')
        plt.xticks(rotation=45)
        plt.tight_layout()

        plot_filename = "university_mentions.png"
        plt.savefig(plot_filename)
        print(f"\n📈 График сохранён как {plot_filename}")
        plt.close()
    else:
        print("\n🔍 Не найдено ни одного сообщения по заданным критериям.")


if __name__ == "__main__":
    main()