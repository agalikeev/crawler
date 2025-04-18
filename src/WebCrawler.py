import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import defaultdict

"""Сбор статистики обработанных страниц для Веб 1.0: общее количество страниц и всех ссылок, 
количество внутренних страниц, количество неработающих страниц, количество внутренних поддоменов, 
общее количество ссылок на внешние ресурсы, количество уникальных внешних ресурсов, 
количество уникальных ссылок на файлы doc/docx/pdf. """


class WebCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.absolute_links = []
        self.links = set()
        self.visited = set()
        self.to_visit = set([base_url])
        self.subdomains = set()
        self.internal_pages = set()
        self.external_resources = set()
        self.external_links = set()
        self.file_types = ['.pdf', '.doc', '.docx']
        self.stats = {
            'total_pages': 0, # страницы без повторов
            'total_links': 0, # все ссылки с повторами +
            'total_internal_pages': 0, # количество внутренних страниц без повторов
            'total_broken_links': 0, # количество страниц с 400 +
            'total_subdomains': 0, # количество поддоменов без повторов
            'total_external_links': 0, # количество ссылок на внешние ресурсы без повторов
            'total_unique_external_resources': 0, # количество уникальных внешних доменов без повторов
            'total_unique_file_links': defaultdict(int)
        }

    def is_internal_netloc(self, netloc: str):
        return netloc == '' or netloc.endswith(self.base_domain)

    def is_file_link(self, link):
        return any(link.lower().endswith(ft) for ft in self.file_types)

    def analyse_link(self, link):
        self.stats['total_links'] += 1
        netloc = urlparse(link).netloc

        if self.is_internal_netloc(netloc):
            self.to_visit.add(link)
            self.internal_pages.add(link)
            self.subdomains.add(netloc)
        else:
            self.external_resources.add(netloc)
            self.external_links.add(link)

        if self.is_file_link(link):
            ext = link.split('.')[-1].lower()
            self.stats['total_unique_file_links'][ext] += 1

    def update_stats(self):
        self.stats['total_subdomains'] = len(self.subdomains)
        self.stats['total_pages'] = len(self.visited)
        self.stats['total_unique_external_resources'] = len(self.external_resources)
        self.stats['total_internal_pages'] = len(self.internal_pages)
        self.stats['total_external_links'] = len(self.external_links)
    def crawl(self, max_pages: int = 100):
        while self.to_visit and len(self.visited) < max_pages:
            url = self.to_visit.pop()
            if url in self.visited:
                continue
            try:
                response = requests.get(self.base_url, timeout=5)
                if response.status_code != 200:
                    self.stats['broken_links'] += 1
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                self.visited.add(url)

                for link in soup.find_all('a', href=True):
                    self.analyse_link(link['href'])
            except Exception as e:
                print(f'Error with url {self.base_url}: {e}')
        self.update_stats()

    def print_stats(self):
        print('total_pages: ', self.stats['total_pages'])  # страницы без повторов
        print('total_links: ', self.stats['total_links'])  # все ссылки с повторами +
        print('total_internal_pages: ', self.stats['total_internal_pages'])  # количество внутренних страниц без повторов
        print('total_broken_links: ', self.stats['total_broken_links'])  # количество страниц с 400 +
        print('total_subdomains: ', self.stats['total_subdomains'])  # количество поддоменов без повторов
        print('total_external_links: ', self.stats['total_external_links'])  # количество ссылок на внешние ресурсы без повторов
        print('total_unique_external_resources: ', self.stats['total_unique_external_resources'])  # количество уникальных внешних доменов без повторов
        print('total_unique_file_links: ', self.stats['total_unique_file_links'])
        print('total_files')
        for ext, count in self.stats['total_unique_file_links'].items():
            print(f"  {ext}: {count}")

wc = WebCrawler('https://spbu.ru/')

print(wc.crawl(max_pages=25))