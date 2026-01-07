import praw
import datetime as dt
import re
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json

# --- Flask + SQLAlchemy app for Laptops (separate DB) ---
laptop_app = Flask(__name__)
laptop_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laptop_reddit_posts.db'
laptop_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

laptop_db = SQLAlchemy(laptop_app)

class RedditPost(laptop_db.Model):
    id = laptop_db.Column(laptop_db.String, primary_key=True)
    subreddit = laptop_db.Column(laptop_db.String(100), nullable=False)
    title = laptop_db.Column(laptop_db.Text, nullable=False)
    score = laptop_db.Column(laptop_db.Integer, nullable=False)
    url = laptop_db.Column(laptop_db.Text, nullable=False)
    num_comments = laptop_db.Column(laptop_db.Integer, nullable=False)
    body = laptop_db.Column(laptop_db.Text, nullable=True)
    created = laptop_db.Column(laptop_db.DateTime, nullable=False)
    cleaned_title = laptop_db.Column(laptop_db.Text, nullable=True)
    cleaned_body = laptop_db.Column(laptop_db.Text, nullable=True)
    sentiment_compound = laptop_db.Column(laptop_db.Float, nullable=True)
    sentiment_label = laptop_db.Column(laptop_db.String(50), nullable=True)
    extracted_laptops = laptop_db.Column(laptop_db.Text, nullable=True)  # JSON string list

    @property
    def laptops(self):
        if self.extracted_laptops:
            try:
                return json.loads(self.extracted_laptops)
            except json.JSONDecodeError:
                return []
        return []

    @laptops.setter
    def laptops(self, laptop_list):
        self.extracted_laptops = json.dumps(laptop_list)

    def __repr__(self):
        return f"<Laptop Post ID: {self.id}>"

# Create tables if they don't exist
with laptop_app.app_context():
    laptop_db.create_all()

# NLTK setup (same lightweight checks as other collector)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
sentiment_analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if not isinstance(text, str) or not text.strip():
        return 0.0, 'neutral'
    scores = sentiment_analyzer.polarity_scores(text)
    compound_score = scores['compound']
    if compound_score >= 0.05:
        label = 'positive'
    elif compound_score <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'
    return compound_score, label

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)  # keep numbers
    tokens = word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return ' '.join(cleaned_tokens)

# Reddit API credentials (re-using existing credentials in the repo)
reddit = praw.Reddit(
    client_id="v3Tqr8fMiFca0UxPErJmCQ",
    client_secret="T4zPUhhtNO9FK9vY7p2877rFeO2SVw",
    user_agent="TrendAnalysisProject by u/TrendsRecommendation",
    username="TrendsRecommendation",
    password="TrendyPassword",
)
print("Authenticated to Reddit for laptop collector.")

# Top 10 laptop-related subreddits (a reasonable selection)
target_subreddits = [
    'laptops',
    'ThinkPad',
    'Surface',
    'macbook',
    'Apple',
    'GamingLaptops',
    'Ultrabooks',
    'LaptopDeals',
    'Lenovo',
    'Acer'
]

post_limit = 1000  # per-subreddit fetch limit (same pattern as phones collector)
new_posts = []

print("Fetching laptop-related posts and preparing to insert into laptop_reddit_posts.db...")
with laptop_app.app_context():
    # load existing ids from the laptop DB to avoid duplicates
    existing_post_ids = {post.id for post in RedditPost.query.with_entities(RedditPost.id).all()}

    for sub in target_subreddits:
        try:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.new(limit=post_limit):
                if post.id not in existing_post_ids:
                    compound, label = get_sentiment(post.title)
                    new_post = RedditPost(
                        id=post.id,
                        subreddit=sub,
                        title=post.title,
                        score=post.score,
                        url=post.url,
                        num_comments=post.num_comments,
                        body=post.selftext,
                        created=dt.datetime.fromtimestamp(post.created_utc),
                        cleaned_title=clean_text(post.title),
                        cleaned_body=clean_text(post.selftext),
                        sentiment_compound=compound,
                        sentiment_label=label,
                        extracted_laptops=None
                    )
                    new_posts.append(new_post)
                    existing_post_ids.add(post.id)
        except Exception as e:
            print(f"Could not process subreddit r/{sub}. Error: {e}")

if new_posts:
    with laptop_app.app_context():
        laptop_db.session.add_all(new_posts)
        laptop_db.session.commit()
    print(f"Inserted {len(new_posts)} new laptop posts into laptop_reddit_posts.db")
else:
    print("No new laptop posts found to insert.")
