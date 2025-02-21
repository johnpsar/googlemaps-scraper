# google_maps_reviews_scraper.py
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from .google_maps_base_scraper import GoogleMapsBaseScraper


class GoogleMapsReviewsScraper(GoogleMapsBaseScraper):
    MAX_RETRY = 5
    MAX_SCROLLS = 40

    def sort_by(self, url, ind):
        self.driver.get(url)
        self._click_on_cookie_agreement()

        wait = WebDriverWait(self.driver, self.MAX_WAIT)
        clicked = False
        tries = 0

        while not clicked and tries < self.MAX_RETRY:
            try:
                menu_bt = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, '//button[@data-value=\'Sort\']')))
                menu_bt.click()
                clicked = True
                time.sleep(3)
            except Exception:
                tries += 1
                self.logger.warning('Failed to click sorting button')

        if tries == self.MAX_RETRY:
            return -1

        recent_rating_bt = self.driver.find_elements(
            By.XPATH, '//div[@role=\'menuitemradio\']')[ind]
        recent_rating_bt.click()
        time.sleep(5)
        return 0

    def get_reviews(self, offset):
        self._scroll()
        time.sleep(4)
        self._expand_reviews()
        self._show_original_reviews()
        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        review_blocks = response.find_all(
            'div', class_='jftiEf fontBodyMedium')

        parsed_reviews = []
        for index, review in enumerate(review_blocks):
            if index >= offset:
                print("index", index)
                r = self._parse_review(review)
                parsed_reviews.append(r)

        return parsed_reviews

    def _show_original_reviews(self):
        translate_buttons = self.driver.find_elements(
            "xpath", "//button[contains(@class, 'kyuRq') and .//span[contains(text(), 'See original')]]")
        for button in translate_buttons:
            self.driver.execute_script("arguments[0].click();", button)

    def _parse_review(self, review):
        return {
            'id_review': review.get('data-review-id'),
            'caption': self._get_review_text(review),
            'relative_date': self._get_relative_date(review),
            'retrieval_date': datetime.now(),
            'rating': self._get_rating(review),
            'username': review.get('aria-label'),
            'n_review_user': self._get_n_reviews(review),
            'url_user': self._get_user_url(review)
        }

    def _scroll(self):
        scrollable_div = self.driver.find_element(
            By.CSS_SELECTOR, 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf')
        self.driver.execute_script(
            'arguments[0].scrollTop = arguments[0].scrollHeight',
            scrollable_div
        )

    def _expand_reviews(self):
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR, 'button.w8nwRe.kyuRq')
        for button in buttons:
            self.driver.execute_script("arguments[0].click();", button)

    # Helper methods for parsing review elements
    def _get_review_text(self, review):
        try:
            return self._filter_string(
                review.find('span', class_='wiI7pd').text
            )
        except:
            return None

    def _get_relative_date(self, review):
        try:
            return review.find('span', class_='rsqaWe').text
        except:
            return None

    def _get_rating(self, review):
        try:
            return float(
                review.find('span', class_='kvMYJc')[
                    'aria-label'].split(' ')[0]
            )
        except:
            return None

    def _get_n_reviews(self, review):
        try:
            return review.find('div', class_='RfnDt').text.split(' ')[3]
        except:
            return 0

    def _get_user_url(self, review):
        try:
            return review.find('button', class_='WEBjve')['data-href']
        except:
            return None
