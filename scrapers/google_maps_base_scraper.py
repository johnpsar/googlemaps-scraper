import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import os
import uuid
import gc
import atexit


class GoogleMapsBaseScraper:
    GM_WEBPAGE = 'https://www.google.com/maps/'
    MAX_WAIT = 10

    def __init__(self, debug=False):
        self.debug = debug
        self.driver = None
        self.user_data_dir = None
        self.logger = self.__get_logger()
        # Register cleanup on program exit
        atexit.register(self.cleanup)
        # Initialize driver
        self.driver = self.__get_driver()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.cleanup()
        return True

    def cleanup(self):
        """Cleanup resources and force garbage collection"""
        try:
            if self.driver:
                self.driver.close()
                self.driver.quit()
                self.driver = None

            # Clean up user data directory if it exists
            if self.user_data_dir and os.path.exists(self.user_data_dir):
                try:
                    import shutil
                    shutil.rmtree(self.user_data_dir)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to remove user data directory: {e}")

            # Force garbage collection
            gc.collect()

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def __get_driver(self):
        options = ChromeOptions()
        if not self.debug:
            options.add_argument("--headless")
        else:
            options.add_argument("--window-size=1366,768")

        # Add unique user data directory
        self.user_data_dir = f"/tmp/chrome-data-{uuid.uuid4()}"
        options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # Additional Chrome options for stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--accept-lang=en-GB")

        try:
            driver = webdriver.Chrome(service=Service(), options=options)
            driver.get(self.GM_WEBPAGE)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to initialize driver: {e}")
            self.cleanup()
            raise

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
        except Exception as e:
            self.logger.warning(f"Failed to click cookie agreement: {e}")
            return False

    @staticmethod
    def _filter_string(str_value):
        return str_value.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
