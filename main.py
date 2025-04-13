import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from collections import defaultdict
import time


class WebCrawler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.to_visit = set([base_url])
        self.stats = {
            'total_pages': 0,
            'total_links': 0,
            'internal_pages': 0,
            'broken_links': 0,
            'subdomains': set(),
            'external_links': set(),
            'file_links': defaultdict(int)
        }

    def is_internal(self, url):
        parsed = urlparse(url)
        return parsed.netloc == self.domain or parsed.netloc == ''

    def is_subdomain(self, url):
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        return parsed.netloc.endswith(self.domain) and parsed.netloc != self.domain

    def is_file_link(self, url):
        file_types = ['.pdf', '.doc', '.docx']
        return any(url.lower().endswith(ft) for ft in file_types)

    def crawl(self, max_pages=100):
        while self.to_visit and self.stats['total_pages'] < max_pages:
            url = self.to_visit.pop()

            if url in self.visited:
                continue

            try:
                response = requests.get(url, timeout=5)
                if response.status_code != 200:
                    self.stats['broken_links'] += 1
                    continue

                self.visited.add(url)
                self.stats['total_pages'] += 1

                soup = BeautifulSoup(response.text, 'html.parser')
                links = [a.get('href') for a in soup.find_all('a', href=True)]

                for link in links:
                    absolute_link = urljoin(url, link)
                    self.stats['total_links'] += 1

                    if self.is_internal(absolute_link):
                        self.stats['internal_pages'] += 1
                        if absolute_link not in self.visited:
                            self.to_visit.add(absolute_link)
                    elif self.is_subdomain(absolute_link):
                        self.stats['subdomains'].add(urlparse(absolute_link).netloc)
                    else:
                        self.stats['external_links'].add(absolute_link)

                    if self.is_file_link(absolute_link):
                        ext = absolute_link.split('.')[-1].lower()
                        self.stats['file_links'][ext] += 1

                time.sleep(1)  # Be polite

            except Exception as e:
                print(f"Error crawling {url}: {e}")
                self.stats['broken_links'] += 1

        return self.stats

    def print_stats(self):
        print(f"Total pages crawled: {self.stats['total_pages']}")
        print(f"Total links found: {self.stats['total_links']}")
        print(f"Internal pages: {self.stats['internal_pages']}")
        print(f"Broken links: {self.stats['broken_links']}")
        print(f"Internal subdomains found: {len(self.stats['subdomains'])}")
        print(f"External links: {len(self.stats['external_links'])}")
        print("File links:")
        for ext, count in self.stats['file_links'].items():
            print(f"  {ext}: {count}")


# Пример использования для СПбГУ
spbu_crawler = WebCrawler("https://spbu.ru/")
spbu_stats = spbu_crawler.crawl(max_pages=3)
spbu_crawler.print_stats()



# # Пример использования для МГУ
# msu_crawler = WebCrawler("https://www.msu.ru/")
# msu_stats = msu_crawler.crawl(max_pages=50)
# msu_crawler.print_stats()