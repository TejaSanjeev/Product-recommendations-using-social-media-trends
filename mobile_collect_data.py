import praw
import datetime as dt
import re
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app import app, db, RedditPost

# NLTK setup and downloads
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
    if not isinstance(text, str) or not text.strip(): return 0.0, 'positive'
    scores = sentiment_analyzer.polarity_scores(text)
    compound_score = scores['compound']
    if compound_score >= 0.05: label = 'positive'
    elif compound_score <= -0.05: label = 'negative'
    else: label = 'positive'
    return compound_score, label

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-z0-9\s]', '', text) # Keep numbers
    tokens = word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return ' '.join(cleaned_tokens)

# Your Reddit API credentials
reddit = praw.Reddit(
    client_id="v3Tqr8fMiFca0UxPErJmCQ",
    client_secret="T4zPUhhtNO9FK9vY7p2877rFeO2SVw",
    user_agent="TrendAnalysisProject by u/TrendsRecommendation",
    username="TrendsRecommendation",
    password="TrendyPassword",
)
print("Successfully authenticated with Reddit.")

target_subreddits = [
    'smartphones',
    'SuggestASmartphone',
    'PickMeAPhone',
    'PickAnAndroidForMe',
    'phones',

    'iphone',
    'GooglePixel',
    'samsung',
    'oneplus',
    'Xiaomi',
    'motorola',

    'IndiaTech',
    'gadgetsindia'
]
post_limit = 1000
new_posts = []

print("Fetching and preparing posts for database...")
with app.app_context():
    existing_post_ids = {post.id for post in RedditPost.query.with_entities(RedditPost.id).all()}

    for sub in target_subreddits:
        try:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.new(limit=post_limit):
                if post.id not in existing_post_ids:
                    compound, label = get_sentiment(post.title)
                    new_post = RedditPost(
                        id=post.id, subreddit=sub, title=post.title,
                        score=post.score, url=post.url, num_comments=post.num_comments,
                        body=post.selftext, created=dt.datetime.fromtimestamp(post.created_utc),
                        cleaned_title=clean_text(post.title),
                        cleaned_body=clean_text(post.selftext),
                        sentiment_compound=compound, sentiment_label=label,
                        extracted_phones=None  # This is intentionally left blank
                    )
                    new_posts.append(new_post)
                    existing_post_ids.add(post.id)
        except Exception as e:
            print(f"Could not process subreddit r/{sub}. Error: {e}")

if new_posts:
    with app.app_context():
        db.session.add_all(new_posts)
        db.session.commit()
    print(f"Successfully inserted {len(new_posts)} new posts into the database.")
else:
    print("No new posts found to insert.")
