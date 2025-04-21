import argparse
from collections import defaultdict
from urllib.parse import urlparse, urljoin
import re

import requests
from bs4 import BeautifulSoup


class WebCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.visited = set()
        self.to_visit = set([base_url])
        self.subdomains = set()
        self.internal_pages = set()
        self.external_resources = set()
        self.file_types = ['.pdf', '.doc', '.docx']
        self.found_files = defaultdict(list)  # Храним найденные файлы по типам
        self.stats = {
            'total_pages': 0,  # страницы без повторов
            'total_links': 0,  # все ссылки с повторами
            'total_internal_pages': 0,  # количество внутренних страниц без повторов
            'total_broken_links': 0,  # количество сломанных страниц
            'total_subdomains': 0,  # количество поддоменов без повторов
            'total_external_links': 0,  # количество ссылок на внешние ресурсы без повторов
            'total_unique_external_resources': 0,  # количество уникальных внешних доменов без повторов
            'total_unique_file_links': defaultdict(int)  # количество документов
        }

    def is_internal_netloc(self, netloc: str):
        return netloc == '' or netloc.endswith(self.base_domain)

    def is_file_link(self, link: str):
        return any(link.lower().endswith(ft) for ft in self.file_types)

    def get_absolute_url(self, base: str, link: str):
        """Преобразует относительную ссылку в абсолютную"""
        if link.startswith('http'):
            return link
        return urljoin(base, link)

    def analyse_link(self, url: str, link: str):
        self.stats['total_links'] += 1
        absolute_link = self.get_absolute_url(url, link)
        parsed = urlparse(absolute_link)

        if self.is_file_link(absolute_link):
            ext = '.' + absolute_link.split('.')[-1].lower()
            self.stats['total_unique_file_links'][ext] += 1
            self.found_files[ext].append(absolute_link)
            return

        if self.is_internal_netloc(parsed.netloc):
            if parsed.netloc and parsed.netloc != self.base_domain:
                self.subdomains.add(parsed.netloc)
            if absolute_link not in self.visited:
                self.to_visit.add(absolute_link)
            self.internal_pages.add(absolute_link)
        else:
            self.external_resources.add(parsed.netloc)
            self.stats['total_external_links'] += 1

    def crawl(self, max_pages: int = 100):
        session = requests.Session()
        session.max_redirects = 5

        while self.to_visit and len(self.visited) < max_pages:
            url = self.to_visit.pop()
            if url in self.visited:
                continue

            try:
                response = session.get(url, timeout=5, allow_redirects=True)
                final_url = response.url

                if response.status_code != 200:
                    self.stats['total_broken_links'] += 1
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                if final_url not in self.visited:
                    self.visited.add(final_url)
                    self.stats['total_pages'] += 1

                for tag in soup.find_all(['a', 'link', 'iframe', 'embed', 'script', 'img']):
                    link = None
                    if tag.name in ['a', 'link'] and tag.has_attr('href'):
                        link = tag['href']
                    elif tag.name in ['iframe', 'embed', 'script', 'img'] and tag.has_attr('src'):
                        link = tag['src']

                    if link:
                        self.analyse_link(url, link)

            except Exception as e:
                print(f'Error with url {url}: {e}')
                self.stats['total_broken_links'] += 1

        self.update_stats()

    def update_stats(self):
        self.stats['total_subdomains'] = len(self.subdomains)
        self.stats['total_internal_pages'] = len(self.internal_pages)
        self.stats['total_unique_external_resources'] = len(self.external_resources)

    def print_stats(self):
        print('\n=== Crawling Statistics ===')
        print(f"Total pages crawled: {self.stats['total_pages']}")
        print(f"Total links found: {self.stats['total_links']}")
        print(f"Internal pages: {self.stats['total_internal_pages']}")
        print(f"Broken links: {self.stats['total_broken_links']}")
        print(f"Subdomains found: {self.stats['total_subdomains']}")
        print(f"External links: {self.stats['total_external_links']}")
        print(f"Unique external domains: {self.stats['total_unique_external_resources']}")
        print(f"Files:")
        for ext, count in self.stats['total_unique_file_links'].items():
            print(f"{ext}: {count} files")


def main(link: str, deep: int):
    wc = WebCrawler(link)
    wc.crawl(max_pages=deep)
    wc.print_stats()


if __name__ == "__main__":
    MAX_DEEP = 10_000

    parser = argparse.ArgumentParser(description='WebCrawler')
    parser.add_argument('link', nargs='?', help='Site link', default='https://spbu.ru/')
    parser.add_argument('--deep', type=int, choices=range(1, MAX_DEEP), help='Search depth', default=10)
    args = parser.parse_args()

    print(f"Crawling {args.link} with depth {args.deep}")
    main(args.link, args.deep)