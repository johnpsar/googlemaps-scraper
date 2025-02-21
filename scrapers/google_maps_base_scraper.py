
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class GoogleMapsBaseScraper:
    GM_WEBPAGE = 'https://www.google.com/maps/'
    MAX_WAIT = 10

    def __init__(self, debug=False):
        self.debug = debug
        self.driver = self.__get_driver()
        self.logger = self.__get_logger()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.driver:
            self.driver.close()
            self.driver.quit()
        return True

    def __get_driver(self):
        options = ChromeOptions()
        if not self.debug:
            options.add_argument("--headless")
        else:
            options.add_argument("--window-size=1366,768")

        options.add_argument("--disable-notifications")
        options.add_argument("--accept-lang=en-GB")

        driver = webdriver.Chrome(service=Service(), options=options)
        driver.get(self.GM_WEBPAGE)
        return driver

    def __get_logger(self):
        logger = logging.getLogger('googlemaps-scraper')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('gm-scraper.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    def _click_on_cookie_agreement(self):
        try:
            agree = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Reject all")]')))
            agree.click()
            return True
        except:
            return False

    @staticmethod
    def _filter_string(str_value):
        return str_value.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
