# google_maps_scraper.py
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import logging
from scrapers.google_maps_reviews_scraper import GoogleMapsReviewsScraper
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SortBy(Enum):
    MOST_RELEVANT = 0
    NEWEST = 1
    HIGHEST_RATING = 2
    LOWEST_RATING = 3


@dataclass
class Review:
    id_review: str
    content: str
    submitted_at: str
    rating: int
    username: str
    n_review_user: int
    avatar: str
    reply_content: str
    reply_date: str
    url_user: str
    source_url: Optional[str] = None


class ReviewsFetcher:
    def __init__(self, debug: bool = False):
        """Initialize the scraper.

        Args:
            debug (bool): If True, runs browser in visible mode
        """
        self.debug = debug
        self.scraper = None

    def __enter__(self):
        self.scraper = GoogleMapsReviewsScraper(debug=self.debug)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        # if self.scraper:
        # self.scraper.close()

    def get_reviews(self,
                    url: str,
                    sort_by: SortBy = SortBy.NEWEST,
                    max_reviews: int = 100) -> List[Review]:
        """
        Scrape reviews from a Google Maps URL.

        Args:
            url (str): Google Maps URL to scrape
            sort_by (SortBy): How to sort the reviews
            max_reviews (int): Maximum number of reviews to fetch

        Returns:
            List[Review]: List of scraped reviews
        """
        if not self.scraper:
            raise RuntimeError("Scraper must be used within a context manager")

        reviews = []
        seen_reviews = set()
        error = self.scraper.sort_by(url, sort_by.value)

        if error != 0:
            logger.error(f"Failed to sort reviews: {error}")
            return reviews

        processed_reviews = 0
        start_index = 0
        while processed_reviews < max_reviews:
            logger.info(
                f"Fetching reviews starting at index {start_index}")

            batch = self.scraper.get_reviews(start_index)
            if not batch:
                logger.info("No more reviews available")
                break

            for review_dict in batch:
                if processed_reviews >= max_reviews:
                    break

                # Check if we've seen this review content + username combination before
                review_key = (review_dict['content'], review_dict['username'])
                if review_key in seen_reviews:
                    logger.info(
                        "Duplicate review found, ending review collection")
                    return reviews

                review = Review(
                    id_review=review_dict['id_review'],
                    content=review_dict['content'],
                    submitted_at=review_dict['submitted_at'],
                    rating=review_dict['rating'],
                    username=review_dict['username'],
                    n_review_user=review_dict['n_review_user'],
                    avatar=review_dict['avatar'],
                    reply_content=review_dict['reply_content'],
                    reply_date=review_dict['reply_date'],
                    url_user=review_dict['url_user'],
                    source_url=url
                )
                if (review.content is not None):
                    seen_reviews.add((review.content, review.username))
                    reviews.append(review)
                    processed_reviews += 1

            start_index += 1

        return reviews

    def get_place_metadata(self, url: str) -> Dict:
        """
        Get metadata about a place.

        Args:
            url (str): Google Maps URL

        Returns:
            Dict: Place metadata
        """
        if not self.scraper:
            raise RuntimeError("Scraper must be used within a context manager")

        return self.scraper.get_account(url)
