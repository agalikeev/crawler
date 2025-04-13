import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from collections import defaultdict
import time

class WebCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.links = [] # мб заменить на set
        self.absolute_links = []
        self.visited = set()
        self.to_visit = set([base_url])
        self.subdomains = set()
        self.stats = {
            'total_pages': 0,
            'total_links': 0,
            'total_internal_pages': 0,
            'total_broken_pages': 0,
            'total_subdomains': 0,
            'total_external_links': 0,
            'total_unique_external_resources': 0,
            'total_unique_file_links_doc': 0,
            'total_unique_file_links_docx': 0,
            'total_unique_file_links_pdf': 0,
        }

    def is_internal_netloc(self, netloc: str):
        return netloc == '' or netloc == self.base_domain

    # def is_file_netloc(self, netloc: str):
    #     file_types = ['.pdf', '.doc', '.docx']
    #     return any(url.lower().endswith(ft) for ft in file_types)

    def crawl(self, max_pages: int=100):
        while self.to_visit and len(self.visited) < max_pages:
            url = self.to_visit.pop()
            if url in self.visited:
                continue

            try:
                response = requests.get(self.base_url, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')  # или 'html.parser'
                self.visited.add(url)
                for link in soup.find_all('a', href=True):

                    self.stats['total_links'] += 1
                    netloc = urlparse(link['href']).netloc

                    if not self.is_internal_netloc(netloc):
                        self.stats['total_external_links'] += 1

                    if netloc.endswith(self.base_domain) and netloc != self.base_domain:
                        self.subdomains.add(netloc)

                    if netloc.endswith(self.base_domain):
                        self.to_visit.add(link['href'])

            except Exception as e:
                print(f'Error with url {self.base_url}: {e}')
            self.stats['total_subdomains'] = len(self.subdomains)

        return self.stats
wc = WebCrawler('https://spbu.ru/')

print(wc.crawl(max_pages=10))