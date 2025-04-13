import vk_api
from vk_api.exceptions import VkApiError
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()


class VKUniversityTracker:
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=os.getenv("VK_ACCESS_TOKEN"))
        self.vk = self.vk_session.get_api()
        self.stats = {
            'total_posts': 0,
            'unique_users': set(),  # Здесь используется множество
            'daily_stats': defaultdict(lambda: {
                'posts': 0,
                'likes': 0,
                'views': 0,
                'comments': 0,
                'reposts': 0
            }),
            'universities': {
                'spbu': {'count': 0, 'posts': []},
                'msu': {'count': 0, 'posts': []}
            }
        }

    def search_posts(self, university_keywords, days=30):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            results = self.vk.newsfeed.search(
                q="|".join(university_keywords),
                start_time=int(start_date.timestamp()),
                end_time=int(end_date.timestamp()),
                count=200,
                extended=1
            )
            self._process_results(results)
        except VkApiError as e:
            print(f"Ошибка VK API: {e}")

    def _process_results(self, results):
        for item in results['items']:
            post_date = datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d')
            university = self._identify_university(item['text'])

            self.stats['total_posts'] += 1
            self.stats['unique_users'].add(item['from_id'])
            self.stats['daily_stats'][post_date]['posts'] += 1
            self.stats['daily_stats'][post_date]['likes'] += item.get('likes', {}).get('count', 0)
            self.stats['daily_stats'][post_date]['views'] += item.get('views', {}).get('count', 0)
            self.stats['daily_stats'][post_date]['comments'] += item.get('comments', {}).get('count', 0)
            self.stats['daily_stats'][post_date]['reposts'] += item.get('reposts', {}).get('count', 0)

            if university:
                self.stats['universities'][university]['count'] += 1
                self.stats['universities'][university]['posts'].append({
                    'id': item['id'],
                    'date': post_date,
                    'text': item['text'][:200] + '...' if len(item['text']) > 200 else item['text'],
                    'likes': item.get('likes', {}).get('count', 0),
                    'views': item.get('views', {}).get('count', 0),
                    'comments': item.get('comments', {}).get('count', 0),
                    'reposts': item.get('reposts', {}).get('count', 0)
                })

    def _identify_university(self, text):
        text = text.lower()
        if any(word in text for word in ['спбгу', 'санкт-петербургский', 'университет', 'ПМ-ПУ']):
            return 'spbu'
        elif any(word in text for word in ['мгу', 'московский государственный']):
            return 'msu'
        return None

    def generate_reports(self):
        """Генерация отчетов и графиков"""
        # Создаем копию для сериализации
        report_data = {
            'total_posts': self.stats['total_posts'],
            'unique_users_count': len(self.stats['unique_users']),
            'unique_users': list(self.stats['unique_users']),  # Преобразуем set в list
            'daily_stats': dict(self.stats['daily_stats']),  # Преобразуем defaultdict в dict
            'universities': self.stats['universities']
        }

        # Сохранение JSON
        with open('vk_university_stats.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        # Графики
        self._create_plots()

        # Excel отчет
        self._generate_excel_report()

    def _create_plots(self):
        dates = sorted(self.stats['daily_stats'].keys())
        posts = [self.stats['daily_stats'][d]['posts'] for d in dates]

        plt.figure(figsize=(12, 6))
        plt.plot(dates, posts, marker='o')
        plt.title('Динамика публикаций по дням')
        plt.xlabel('Дата')
        plt.ylabel('Количество публикаций')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('posts_dynamics.png')
        plt.close()

        uni_counts = [
            self.stats['universities']['spbu']['count'],
            self.stats['universities']['msu']['count']
        ]

        plt.figure(figsize=(8, 8))
        plt.pie(uni_counts, labels=['СПбГУ', 'МГУ'], autopct='%1.1f%%')
        plt.title('Распределение упоминаний университетов')
        plt.savefig('universities_distribution.png')
        plt.close()

    def _generate_excel_report(self):
        with pd.ExcelWriter('vk_university_report.xlsx') as writer:
            # Сводка
            summary_data = {
                'Метрика': ['Всего публикаций', 'Уникальных пользователей',
                            'Упоминаний СПбГУ', 'Упоминаний МГУ'],
                'Значение': [
                    self.stats['total_posts'],
                    len(self.stats['unique_users']),
                    self.stats['universities']['spbu']['count'],
                    self.stats['universities']['msu']['count']
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Сводка', index=False)

            # По дням
            daily_data = []
            for date, stats in self.stats['daily_stats'].items():
                daily_data.append({
                    'Дата': date,
                    'Публикации': stats['posts'],
                    'Лайки': stats['likes'],
                    'Просмотры': stats['views'],
                    'Комментарии': stats['comments'],
                    'Репосты': stats['reposts']
                })
            pd.DataFrame(daily_data).to_excel(writer, sheet_name='По дням', index=False)

            # Примеры публикаций
            posts_data = []
            for uni in ['spbu', 'msu']:
                for post in self.stats['universities'][uni]['posts'][:10]:
                    posts_data.append({
                        'Университет': 'СПбГУ' if uni == 'spbu' else 'МГУ',
                        'Дата': post['date'],
                        'Текст': post['text'],
                        'Лайки': post['likes'],
                        'Просмотры': post['views'],
                        'Комментарии': post['comments'],
                        'Репосты': post['reposts']
                    })
            pd.DataFrame(posts_data).to_excel(writer, sheet_name='Примеры публикаций', index=False)


if __name__ == "__main__":
    tracker = VKUniversityTracker()

    spbu_keywords = ["СПбГУ", "Санкт-Петербургский университет","университет", "ПМ-ПУ"]
    msu_keywords = ["МГУ", "Московский государственный университет"]

    print("🚀 Начинаем сбор данных из VK...")
    tracker.search_posts(spbu_keywords + msu_keywords, days=30)

    print("📊 Генерация отчетов...")
    tracker.generate_reports()

    print("✅ Готово! Отчеты сохранены в файлах:")
    print("- vk_university_stats.json")
    print("- vk_university_report.xlsx")
    print("- posts_dynamics.png")
    print("- universities_distribution.png")