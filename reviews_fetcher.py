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
        if self.scraper:
            self.scraper.cleanup()
            self.scraper = None

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
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                error = self.scraper.sort_by(url, sort_by.value)
                if error != 0:
                    logger.error(f"Failed to sort reviews: {error}")
                    return reviews
                break
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error during sort_by (attempt {retry_count}/{max_retries}): {str(e)}")
                if retry_count == max_retries:
                    logger.error("Max retries reached for sort_by operation")
                    return reviews
                # Try to reinitialize the scraper
                try:
                    self.scraper.cleanup()
                    self.scraper = GoogleMapsReviewsScraper(debug=self.debug)
                except Exception as cleanup_error:
                    logger.error(
                        f"Error during scraper reinitialization: {str(cleanup_error)}")
                    return reviews

        processed_reviews = 0
        start_index = 0
        consecutive_failures = 0
        max_consecutive_failures = 3

        while processed_reviews < max_reviews:
            try:
                logger.info(
                    f"Fetching reviews starting at index {start_index}")

                batch = self.scraper.get_reviews(start_index)
                if not batch:
                    logger.info("No more reviews available")
                    break

                consecutive_failures = 0  # Reset on successful batch
                for review_dict in batch:
                    if processed_reviews >= max_reviews:
                        break

                    # Check if we've seen this review content + username combination before
                    review_key = (review_dict['content'],
                                  review_dict['username'])
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

            except Exception as e:
                consecutive_failures += 1
                logger.error(
                    f"Error fetching reviews (attempt {consecutive_failures}/{max_consecutive_failures}): {str(e)}")

                if consecutive_failures >= max_consecutive_failures:
                    logger.error(
                        "Max consecutive failures reached, stopping review collection")
                    break

                # Try to reinitialize the scraper
                try:
                    self.scraper.cleanup()
                    self.scraper = GoogleMapsReviewsScraper(debug=self.debug)
                    # Retry the sort operation
                    error = self.scraper.sort_by(url, sort_by.value)
                    if error != 0:
                        logger.error(
                            "Failed to re-sort reviews after reinitialization")
                        break
                except Exception as cleanup_error:
                    logger.error(
                        f"Error during scraper reinitialization: {str(cleanup_error)}")
                    break

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

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                return self.scraper.get_account(url)
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"Error getting place metadata (attempt {retry_count}/{max_retries}): {str(e)}")

                if retry_count == max_retries:
                    logger.error("Max retries reached for get_place_metadata")
                    raise

                # Try to reinitialize the scraper
                try:
                    self.scraper.cleanup()
                    self.scraper = GoogleMapsReviewsScraper(debug=self.debug)
                except Exception as cleanup_error:
                    logger.error(
                        f"Error during scraper reinitialization: {str(cleanup_error)}")
                    raise
