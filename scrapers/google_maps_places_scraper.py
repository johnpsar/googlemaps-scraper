# google_maps_places_scraper.py
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import pandas as pd
import itertools
import time
from .google_maps_base_scraper import GoogleMapsBaseScraper


class GoogleMapsPlacesScraper(GoogleMapsBaseScraper):

    def get_places(self, keyword_list=None):
        df_places = pd.DataFrame()
        search_point_url_list = self._gen_search_points_from_square(
            keyword_list=keyword_list)

        for i, search_point_url in enumerate(search_point_url_list):
            try:
                places_data = self._scrape_places_from_url(search_point_url)
                df_places = df_places.append(places_data, ignore_index=True)

                if (i+1) % 10 == 0:
                    self._save_places_data(df_places)
            except Exception as e:
                self.logger.error(
                    f"Error scraping {search_point_url}: {str(e)}")

        return df_places

    def get_place_details(self, url):
        self.driver.get(url)
        self._click_on_cookie_agreement()
        time.sleep(2)

        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        return self._parse_place(response, url)

    def _scrape_places_from_url(self, url):
        try:
            self.driver.get(url)
        except NoSuchElementException:
            self.driver.quit()
            self.driver = self._get_driver()
            self.driver.get(url)

        self._scroll_results()

        response = BeautifulSoup(self.driver.page_source, 'html.parser')
        div_places = response.select('div[jsaction] > a[href]')

        return [self._parse_place_basic_info(div_place, url)
                for div_place in div_places]

    def _scroll_results(self):
        scrollable_div = self.driver.find_element(
            By.CSS_SELECTOR,
            "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd > div[aria-label*='Results for']"
        )
        for _ in range(10):
            self.driver.execute_script(
                'arguments[0].scrollTop = arguments[0].scrollHeight',
                scrollable_div
            )
            time.sleep(0.5)

    def _parse_place_basic_info(self, div_place, search_url):
        return {
            'search_point_url': search_url.replace(
                'https://www.google.com/maps/search/', ''
            ),
            'href': div_place['href'],
            'name': div_place['aria-label']
        }

    def _parse_place(self, response, url):
        # ... (keep the existing __parse_place method, but rename it)
        pass

    def _gen_search_points_from_square(self, keyword_list=None):
        # ... (keep the existing _gen_search_points_from_square method)
        pass

    @staticmethod
    def _save_places_data(df_places):
        df_places = df_places[['search_point_url', 'href', 'name']]
        df_places.to_csv('output/places_wax.csv', index=False)
