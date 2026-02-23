# crawlerbot/middlewares.py

from scrapy import signals
from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumMiddlewareCompat:
    """
    Scrapy + Selenium downloader middleware
    """

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=chrome_options)

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(
            middleware.spider_closed,
            signal=signals.spider_closed
        )
        return middleware

    def process_request(self, request, spider):
        self.driver.get(request.url)

        # attach driver to request meta (NOT response)
        request.meta["driver"] = self.driver

        body = self.driver.page_source.encode("utf-8")

        return HtmlResponse(
            url=request.url,
            body=body,
            encoding="utf-8",
            request=request,
        )

    def spider_closed(self, spider):
        if self.driver:
            self.driver.quit()