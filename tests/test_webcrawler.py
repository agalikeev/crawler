import pytest
from src.WebCrawler import WebCrawler
import requests

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
    assert crawler.stats['total_internal_pages'] == 1

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
    assert crawler.stats['total_subdomains'] == 1

def test_max_pages_limit(requests_mock):
    """Тест ограничения по количеству страниц"""
    base_url = "http://test.com"
    requests_mock.get(base_url, text="<a href='/page1'>Page 1</a>")
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler(base_url)
    crawler.crawl(max_pages=1)
    
    assert len(crawler.visited) == 1  # Только главная страница

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
    assert crawler.stats['total_internal_pages'] == 1
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
    
    assert crawler.stats['total_links'] == 2 
    assert crawler.stats['total_internal_pages'] == 1 # только одна внутренняя(без повтора) 


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

def test_cyclic_links_handling(requests_mock):
    """Тест обработки циклических ссылок"""
    requests_mock.get("http://test.com", text="<a href='/page1'>Link</a>")
    requests_mock.get("http://test.com/page1", text="<a href='/'>Home</a>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=3)

    assert len(crawler.visited) == 2 

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
    """Тест обработки страниц с разными кодировками(windows-1251)"""
    requests_mock.get("http://test.com", content="<a href='/page1'>Ссылка</a>".encode('windows-1251'),
                     headers={'Content-Type': 'text/html; charset=windows-1251'})
    requests_mock.get("http://test.com/page1", text="OK")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=2)
    
    assert "http://test.com/page1" in crawler.internal_pages

def test_wrong_file(requests_mock):
    """Тест неправильного файла(не pdf, doc, docx). Не должно учитываться"""
    requests_mock.get("http://test.com", text="""
    <html>
        <a href='/file.pdf'>PDF</a>
        <a href='/file.doc'>DOC</a>
        <a href='/file.docx'>DOCX</a>
        <a href='/file.txt'>TXT</a>
    </html>
    """)
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_unique_file_links']['.pdf'] == 1
    assert crawler.stats['total_unique_file_links']['.doc'] == 1
    assert crawler.stats['total_unique_file_links']['.docx'] == 1
    assert '.txt' not in crawler.stats['total_unique_file_links']  # TXT не должен учитываться
   
def test_wrong_url(requests_mock):
    """Тест неправильного URL"""
    requests_mock.get("http://test.com", text="<html> <h1> hello </h1> </html>")

    base_url = "wrong_url"
    crawler = WebCrawler(base_url)
    crawler.crawl(max_pages=1)

    assert crawler.stats["total_broken_links"] == 1

def test_excessive_max_pages(requests_mock):
    """проход с излишним количеством страниц"""
    requests_mock.get("http://test.com", text="<a href='/page1'>Link</a>")

    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=100_000)

    assert crawler.stats["total_internal_pages"] == 1 # не должно ломаться

def test_invalid_html_handling(requests_mock):
    """Тест обработки некорректного HTML"""
    requests_mock.get("http://test.com", text="<html> <a href='/page1'>Link </html>")  # Незакрытый тег
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_links'] == 1

def test_connection_timeout(requests_mock):
    """Тест обработки таймаута соединения"""
    requests_mock.get("http://test.com", exc=requests.exceptions.ConnectTimeout)
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_broken_links'] == 1 # засчиталась как битая
    assert len(crawler.visited) == 0 # но не засчиталась как посещенная
   
def test_mailto_links_handling(requests_mock):
    """Тест обработки mailto ссылок"""
    requests_mock.get("http://test.com", text="<a href='mailto:test@example.com'>Email</a>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_links'] == 1
    assert len(crawler.external_resources) == 0  # mailto не считается внешним ресурсом

# TODO: почему total_links == 0 
def test_empty_links_handling(requests_mock):
    """Тест обработки пустых ссылок"""
    requests_mock.get("http://test.com", text="<a href=''>Empty link</a>")
    
    crawler = WebCrawler("http://test.com")
    crawler.crawl(max_pages=1)
    
    assert crawler.stats['total_links'] == 2
    assert crawler.stats['total_broken_links'] == 0  # Пустая != битая

if __name__ == "__main__":
    pass