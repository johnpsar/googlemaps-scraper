from flask import Flask, request, jsonify
from reviews_fetcher import ReviewsFetcher, SortBy

app = Flask(__name__)


@app.route('/api/fetch-reviews', methods=['GET'])
def fetch_reviews():
    try:
        # Get parameters from the request
        place_id = request.args.get('place_id')
        max_reviews = request.args.get('max_reviews', default=10, type=int)

        print("Place id", place_id)
        print("Max reviews", max_reviews)
        # Validate place_id
        if not place_id:
            return jsonify({'error': 'place_id is required'}), 400

        # Construct the URL
        url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

        # Fetch reviews using the scraper
        with ReviewsFetcher(debug=False) as scraper:
            reviews = scraper.get_reviews(
                url=url,
                sort_by=SortBy.NEWEST,
                max_reviews=max_reviews
            )

            # Convert reviews to dictionary format
            reviews_data = []
            for review in reviews:
                reviews_data.append({
                    'id': review.id_review,
                    'content': review.content,
                    'submitted_at': review.submitted_at,
                    'rating': review.rating,
                    'username': review.username,
                    'avatar': review.avatar,
                    'reply_content': review.reply_content,
                    'reply_date': review.reply_date,
                    'n_review_user': review.n_review_user,
                    'url_user': review.url_user,
                })

            review_with_text = [
                review for review in reviews_data if review['content'] != None]

            return jsonify({
                'success': True,
                'total_reviews': len(reviews_data),
                'reviews': reviews_data,
                'total_review_with_text': len(review_with_text),
                'review_with_text': review_with_text
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
