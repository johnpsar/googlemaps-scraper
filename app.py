from flask import Flask, request, jsonify
from reviews_fetcher import ReviewsFetcher, SortBy
from werkzeug.middleware.proxy_fix import ProxyFix
import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')
file_handler = RotatingFileHandler(
    'logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Google Maps Reviews Scraper startup')

# Global error handlers


@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/fetch-reviews', methods=['GET'])
def fetch_reviews():
    try:
        # Get parameters from the request
        place_id = request.args.get('place_id')
        max_reviews = request.args.get('max_reviews', default=10, type=int)

        # Input validation
        if not place_id:
            return jsonify({'error': 'place_id is required'}), 400
        if max_reviews < 1 or max_reviews > 1000:
            return jsonify({'error': 'max_reviews must be between 1 and 1000'}), 400

        app.logger.info(
            f'Fetching reviews for place_id: {place_id}, max_reviews: {max_reviews}')

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
                review for review in reviews_data if review['content'] is not None]

            app.logger.info(
                f'Successfully fetched {len(reviews_data)} reviews')
            return jsonify({
                'success': True,
                'total_reviews': len(reviews_data),
                'reviews': reviews_data,
                'total_review_with_text': len(review_with_text),
                'review_with_text': review_with_text
            })

    except Exception as e:
        app.logger.error(f'Error fetching reviews: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching reviews'
        }), 500


if __name__ == '__main__':
    # For development only
    app.run(host='0.0.0.0', port=5000, debug=False)
