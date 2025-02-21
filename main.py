from reviews_fetcher import ReviewsFetcher, SortBy


def main():
    place_id = 'ChIJ_5LxRO2ZoRQRE1Q7-KhVZpM'
    url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    print("Fetching reviews for url:", url)
    # Use the scraper within a context manager
    with ReviewsFetcher(debug=False) as scraper:
        # Get reviews
        reviews = scraper.get_reviews(
            url=url,
            sort_by=SortBy.NEWEST,
            max_reviews=10
        )

        # Print results
        print(f"Found {len(reviews)} reviews:")
        for review in reviews:
            print(f"\nReview by {review.username}")
            print(f"Rating: {review.rating}/5")
            print(f"Comment: {review.caption}")
            print(f"Date: {review.relative_date}")


if __name__ == "__main__":
    main()
