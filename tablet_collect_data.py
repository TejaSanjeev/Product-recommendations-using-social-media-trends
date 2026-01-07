import praw
import datetime as dt
import re
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json

# --- Flask + SQLAlchemy app for Tablets (separate DB) ---
tablet_app = Flask(__name__)
tablet_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tablet_reddit_posts.db'
tablet_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

tablet_db = SQLAlchemy(tablet_app)

class RedditPost(tablet_db.Model):
    id = tablet_db.Column(tablet_db.String, primary_key=True)
    subreddit = tablet_db.Column(tablet_db.String(100), nullable=False)
    title = tablet_db.Column(tablet_db.Text, nullable=False)
    score = tablet_db.Column(tablet_db.Integer, nullable=False)
    url = tablet_db.Column(tablet_db.Text, nullable=False)
    num_comments = tablet_db.Column(tablet_db.Integer, nullable=False)
    body = tablet_db.Column(tablet_db.Text, nullable=True)
    created = tablet_db.Column(tablet_db.DateTime, nullable=False)
    cleaned_title = tablet_db.Column(tablet_db.Text, nullable=True)
    cleaned_body = tablet_db.Column(tablet_db.Text, nullable=True)
    sentiment_compound = tablet_db.Column(tablet_db.Float, nullable=True)
    sentiment_label = tablet_db.Column(tablet_db.String(50), nullable=True)
    extracted_tablets = tablet_db.Column(tablet_db.Text, nullable=True)  # JSON string list

    @property
    def tablets(self):
        if self.extracted_tablets:
            try:
                return json.loads(self.extracted_tablets)
            except json.JSONDecodeError:
                return []
        return []

    @tablets.setter
    def tablets(self, tablet_list):
        self.extracted_tablets = json.dumps(tablet_list)

    def __repr__(self):
        return f"<Tablet Post ID: {self.id}>"

# Create tables if they don't exist
with tablet_app.app_context():
    tablet_db.create_all()

# NLTK setup (lightweight checks)
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
    client_id="",
    client_secret="",
    user_agent="",
    username="",
    password="",
)
print("Authenticated to Reddit for tablet collector.")

# Top 10 tablet-related subreddits (reasonable selection)
target_subreddits = [
    'tablets',
    'ipad',
    'Surface',
    'Apple',
    'AndroidTablets',
    'Samsung',
    'GalaxyTab',
    'tabletdeals',
    'lenovo',
    'Xiaomi',       
    'MiPad',        
    'oneplus'        
]

post_limit = 1000  # per-subreddit fetch limit
new_posts = []

print("Fetching tablet-related posts and preparing to insert into tablet_reddit_posts.db...")
with tablet_app.app_context():
    # load existing ids from the tablet DB to avoid duplicates
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
                        extracted_tablets=None
                    )
                    new_posts.append(new_post)
                    existing_post_ids.add(post.id)
        except Exception as e:
            print(f"Could not process subreddit r/{sub}. Error: {e}")

if new_posts:
    with tablet_app.app_context():
        tablet_db.session.add_all(new_posts)
        tablet_db.session.commit()
    print(f"Inserted {len(new_posts)} new tablet posts into tablet_reddit_posts.db")
else:
    print("No new tablet posts found to insert.")
