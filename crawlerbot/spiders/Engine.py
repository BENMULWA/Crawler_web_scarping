import scrapy
import json
import re
from datetime import datetime
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twisted.internet.error import TimeoutError, TCPTimedOutError

class FXSpider(scrapy.Spider):
    name = "engine"
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 15,  # allow slower pages
        "RETRY_ENABLED": False,  # no automatic retries
        "CONCURRENT_REQUESTS": 5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 5,
    }

    supported_currency = ["USD", "UGX", "TZS", "KES", "ZAR", "GBP", "EUR"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Connect to MongoDB
        client = MongoClient(
            "mongodb+srv://scrapy-selenium:benard9507@cluster0.xad7ngd.mongodb.net/?retryWrites=true&w=majority"
        )
        db = client["Currency_ratesDB_Crawler"]
        self.collection = db["CrawlerBot_Scraping data"]

        # Selenium headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)

        # dictionary to store rates
        self.fx_dict = {}

    def start_requests(self):
        for base in self.supported_currency:
            for target in self.supported_currency:
                if base != target:
                    url = f"https://www.xe.com/currencyconverter/convert/?Amount=1&From={base}&To={target}"
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse,
                        meta={"base": base, "target": target},
                        dont_filter=True,
                        errback=self.handle_error,
                    )

    def parse(self, response):
        base = response.meta["base"]
        target = response.meta["target"]

        try:
            self.driver.get(response.url)

            # Wait for the rates JS to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//script[contains(text(),'initialRatesData')]"))
            )

            sel = Selector(text=self.driver.page_source)
            script = sel.xpath("//script[contains(text(),'initialRatesData')]/text()").get()

            if not script:
                self.logger.warning(f"No rate data for {base}->{target}")
                return

            # Extract JSON rates
            match = re.search(r'"rates":({.*?})', script)
            if not match:
                self.logger.warning(f"No JSON rates for {base}->{target}")
                return

            rates = json.loads(match.group(1))
            rate = rates.get(target)
            if rate is None:
                self.logger.warning(f"Rate missing {base}->{target}")
                return

            # Save exact rate
            self.fx_dict.setdefault(base, {})[target] = float(rate)
            self.logger.info(f"✅ {base}->{target}: {rate}")

        except Exception as e:
            self.logger.warning(f"Could not fetch rate for {base}->{target}: {e}")

    def handle_error(self, failure):
        if failure.check(TimeoutError, TCPTimedOutError):
            self.logger.warning(f"Request timed out: {failure.request.url}")

    def close(self, reason):
        # Insert a new document per run with timestamp
        final_doc = {"_id": f"fx_rates_{datetime.utcnow().isoformat()}"}
        final_doc.update(self.fx_dict)

        self.collection.insert_one(final_doc)

        # Save backup JSON
        with open(f"fx_rates_{datetime.utcnow().isoformat()}.json", "w") as f:
            json.dump(final_doc, f, indent=4)

        self.driver.quit()
        self.logger.info(f"✅ FX rates saved for run {final_doc['_id']}! Total bases: {len(self.fx_dict)}")