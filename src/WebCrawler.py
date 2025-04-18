import argparse
from collections import defaultdict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


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
            'total_pages': 0,  # страницы без повторов
            'total_links': 0,  # все ссылки с повторами
            'total_internal_pages': 0,  # количество внутренних страниц без повторов
            'total_broken_links': 0,  # количество сломанных страниц
            'total_subdomains': 0,  # количество поддоменов без повторов
            'total_external_links': 0,  # количество ссылок на внешние ресурсы с повторами
            'total_unique_external_resources': 0,  # количество уникальных внешних доменов без повторов
            'total_unique_file_links': defaultdict(int)  # количество документов
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
            self.stats['total_external_links'] += 1

        if self.is_file_link(link):
            ext = link.split('.')[-1].lower()
            self.stats['total_unique_file_links'][ext] += 1

    def update_stats(self):
        self.stats['total_subdomains'] = len(self.subdomains)
        self.stats['total_pages'] = len(self.visited)
        self.stats['total_unique_external_resources'] = len(self.external_resources)
        self.stats['total_internal_pages'] = len(self.internal_pages)

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
        print('total_pages: ', self.stats['total_pages'])
        print('total_links: ', self.stats['total_links'])
        print('total_internal_pages: ',
              self.stats['total_internal_pages'])
        print('total_broken_links: ', self.stats['total_broken_links'])
        print('total_subdomains: ', self.stats['total_subdomains'])
        print('total_external_links: ',
              self.stats['total_external_links'])
        print('total_unique_external_resources: ',
              self.stats['total_unique_external_resources'])
        print('total_unique_file_links: ', self.stats['total_unique_file_links'])
        print('total_files')
        for ext, count in self.stats['total_unique_file_links'].items():
            print(f"  {ext}: {count}")


def main(link, deep):
    wc = WebCrawler(link)
    wc.crawl(max_pages=deep)
    wc.print_stats()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WebCrawler')

    parser.add_argument('link', nargs='?', help='Site link', default='https://spbu.ru/')
    parser.add_argument('--deep', help='Search deep', default='10')

    args = parser.parse_args()
    main(args.link, args.deep)
