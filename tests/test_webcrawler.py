import pytest
from src.WebCrawler import WebCrawler  # Импортируйте ваш класс
from urllib.parse import urlparse
import requests
import os

# ====================== Тесты с requests-mock ======================
def test_base_url_initialization(requests_mock):
    """Тест инициализации базового URL"""
    requests_mock.get("http://test.com", text="<html></html>")
    crawler = WebCrawler("http://test.com")
    assert crawler.base_url == "http://test.com"
    assert crawler.base_domain == "test.com"

def test_internal_link_index(requests_mock):
    """Тест обработки внутренних ссылок когда их нет"""
    requests_mock.get("http://test.com", text="base index")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    # assert "http://test.com" in crawler.internal_pages
    assert crawler.stats['total_internal_pages'] == 0

def test_internal_link_parsing(requests_mock):
    """Тест обработки внутренних ссылок"""
    requests_mock.get("http://test.com", text="<a href='/page1'>Link</a>")
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert "http://test.com/page1" in crawler.internal_pages
    assert crawler.stats['total_internal_pages'] == 1 # 2

def test_external_link_detection(requests_mock):
    """Тест обнаружения внешних ссылок"""
    requests_mock.get("http://test.com", text="<a href='http://external.com'>External</a>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert "external.com" in crawler.external_resources
    assert crawler.stats['total_external_links'] == 1

def test_file_link_detection(requests_mock):
    """Тест обнаружения файловых ссылок"""
    requests_mock.get("http://test.com", text="<a href='/doc.pdf'>PDF</a>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_unique_file_links']['.pdf'] == 1
    assert "/doc.pdf" in crawler.found_files['.pdf'][0]

def test_broken_link_handling(requests_mock):
    """Тест обработки битых ссылок"""
    requests_mock.get("http://test.com", status_code=404)
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_broken_links'] == 1
    assert len(crawler.visited) == 0

def test_subdomain_detection(requests_mock):
    """Тест обнаружения поддоменов"""
    base_url = "http://test.com"
    requests_mock.get(base_url, text="<a href='http://sub.test.com'>Subdomain</a>")
    
    crawler = WebCrawler(base_url)
    crawler.crawl(max_pages=1)
    
    assert "sub.test.com" in crawler.subdomains
    assert crawler.stats['total_subdomains'] == 1  # Исправлена опечатка (было 'subdomains')

def test_max_pages_limit(requests_mock):
    """Тест ограничения по количеству страниц"""
    base_url = "http://test.com"
    requests_mock.get(base_url, text="<a href='/page1'>Page 1</a>")
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler(base_url)
    crawler.crawl(max_pages=1)
    
    assert len(crawler.visited) == 1  # Только главная страница (max_pages=1)

# TODO: тут ссылка берется изначальная, а не та на которую редиректиться
def test_redirect_handling(requests_mock):
    """Тест обработки редиректов"""
    base_url = "http://test.com"
    requests_mock.get(base_url, text="<a href='/redirect'>Redirect</a>")
    requests_mock.get(
        "http://test.com/redirect",
        status_code=302,
        headers={"Location": "/target"},
        text=""
    )
    requests_mock.get("http://test.com/target", text="OK")
    
    crawler = WebCrawler(base_url)
    crawler.crawl(max_pages=2)
    
    
    assert "http://test.com/target" in crawler.visited
    # assert "http://test.com/redirect" in crawler.visited

# ====================== Параметризованные тесты ======================
# TODO: Это что за хуйня???
# @pytest.mark.parametrize("url, expected", [
#     ("#anchor", False),  # Якорь не должен учитываться
#     ("javascript:void(0)", False),  # JS-ссылка
#     ("mailto:test@example.com", False),  # Почта
#     ("tel:+123456789", False),  # Телефон
#     ("/relative", True),  # Относительная ссылка
# ])
# def test_weird_links(requests_mock, url, expected):
#     """Тест обработки нестандартных ссылок"""
#     requests_mock.get("http://test.com", text=f"<a href='{url}'>Link</a>")
    
#     crawler = WebCrawler("http://test.com")
#     crawler.crawl(max_pages=1)
    
#     assert (crawler.stats['total_links'] == 1) == expected

# ====================== Тесты статистики ======================
def test_stats_calculation(requests_mock):
    """Тест корректности расчета статистики"""
    requests_mock.get("http://test.com", text="""
    <html>
        <a href='/page1'>Page 1</a>
        <a href='http://external.com'>External</a>
        <a href='/doc.pdf'>PDF</a>
    </html>
    """)
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert crawler.stats['total_pages'] == 2
    assert crawler.stats['total_links'] == 3
    assert crawler.stats['total_internal_pages'] == 1 # 2
    assert crawler.stats['total_external_links'] == 1
    assert crawler.stats['total_unique_file_links']['.pdf'] == 1

def test_empty_page_handling(requests_mock):
    """Тест обработки пустой страницы"""
    requests_mock.get("http://test.com", text="<html></html>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_links'] == 0
    assert len(crawler.visited) == 1

def test_duplicate_links_handling(requests_mock):
    """Тест обработки дублирующихся ссылок"""
    requests_mock.get("http://test.com", text="<a href='/page1'>Link</a><a href='/page1'>Link</a>")
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert crawler.stats['total_links'] == 2  # Две ссылки в HTML
    assert crawler.stats['total_internal_pages'] == 1 # Главная + page1 = 2 # 

# new

def test_relative_links_without_slash(requests_mock):
    """Тест обработки относительных ссылок без начального слэша"""
    requests_mock.get("http://test.com", text="<a href='page1'>Link</a>")
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert "http://test.com/page1" in crawler.internal_pages

def test_links_with_query_params(requests_mock):
    """Тест обработки ссылок с параметрами запроса"""
    requests_mock.get("http://test.com", text="<a href='/page?param=value'>Link</a>")
    requests_mock.get("http://test.com/page?param=value", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert "http://test.com/page?param=value" in crawler.internal_pages

def test_different_schemes_handling(requests_mock):
    """Тест обработки ссылок с разными схемами (http/https)"""
    requests_mock.get("http://test.com", text="<a href='https://test.com/secure'>Secure</a>")
    requests_mock.get("https://test.com/secure", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert "https://test.com/secure" in crawler.internal_pages


# TODO: тут на главной странице ссылка на другую(на которой ссылка на главную) -> assert 3  != 2
# crawler.visited = set(['http://test.com/page1', 'http://test.com', 'http://test.com/'])
def test_cyclic_links_handling(requests_mock):
    """Тест обработки циклических ссылок"""
    requests_mock.get("http://test.com", text="<a href='/page1'>Link</a>")
    requests_mock.get("http://test.com/page1", text="<a href='/'>Home</a>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=3)

    assert len(crawler.visited) == 2  # Должен остановиться, несмотря на цикл

def test_links_in_different_tags(requests_mock):
    """Тест обработки ссылок в разных HTML-тегах"""
    requests_mock.get("http://test.com", text="""
    <html>
        <link href="/style.css" rel="stylesheet">
        <script src="/script.js"></script>
        <img src="/image.jpg">
        <iframe src="/frame.html"></iframe>
    </html>
    """)
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_links'] == 4

def test_encoding_handling(requests_mock):
    """Тест обработки страниц с разными кодировками"""
    requests_mock.get("http://test.com", content="<a href='/page1'>Ссылка</a>".encode('windows-1251'),
                     headers={'Content-Type': 'text/html; charset=windows-1251'})
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert "http://test.com/page1" in crawler.internal_pages


if __name__ == "__main__":
    pass