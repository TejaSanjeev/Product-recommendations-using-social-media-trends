from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import json
from collections import Counter
import re
import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reddit_posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB setup
db = SQLAlchemy(app)

class RedditPost(db.Model):
    id = db.Column(db.String, primary_key=True)
    subreddit = db.Column(db.String(100), nullable=False)
    title = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=False)
    num_comments = db.Column(db.Integer, nullable=False)
    body = db.Column(db.Text, nullable=True)
    created = db.Column(db.DateTime, nullable=False)
    cleaned_title = db.Column(db.Text, nullable=True)
    cleaned_body = db.Column(db.Text, nullable=True)
    sentiment_compound = db.Column(db.Float, nullable=True)
    sentiment_label = db.Column(db.String(50), nullable=True)
    extracted_phones = db.Column(db.Text, nullable=True)  # Will store a JSON string list

    @property
    def phones(self):
        if self.extracted_phones:
            try:
                return json.loads(self.extracted_phones)
            except json.JSONDecodeError:
                return []
        return []

    @phones.setter
    def phones(self, phone_list):
        self.extracted_phones = json.dumps(phone_list)

    def __repr__(self):
        return f"<Post ID: {self.id}>"

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    # You will need to create a basic index.html in a 'templates' folder
    return "<h1>Trend Analysis Project</h1><p>Navigate to /api/trends to see results.</p>"

@app.route('/api/reddit-posts')
def api_reddit_posts():
    posts = RedditPost.query.order_by(RedditPost.created.desc()).limit(20).all()
    results = [
        {
            'id': post.id,
            'subreddit': post.subreddit,
            'title': post.title,
            'score': post.score,
            'url': post.url,
            'num_comments': post.num_comments,
            'sentiment': post.sentiment_label,
            'extracted_phones': post.phones
        } for post in posts
    ]
    return jsonify(results)

@app.route('/api/trends')
def api_trends():
    """
    This endpoint now correctly aggregates phone names from all processed posts
    and returns a ranked list of the most mentioned products.
    """
    all_phones = []
    # Filter for posts where extraction has been completed
    posts = RedditPost.query.filter(RedditPost.extracted_phones != None).all()
    for post in posts:
        all_phones.extend(post.phones)
    
    if not all_phones:
        return jsonify({"message": "No trends found yet. Run the extraction script."})
        
    trend_counts = Counter(all_phones)
    return jsonify(trend_counts.most_common(30))

if __name__ == '__main__':
    app.run(debug=True)
