# Save this as analyze_trends.py

import spacy
from collections import Counter
from app import app, db, RedditPost # Import components from our Flask app

def analyze_product_trends():
    """
    Analyzes positive/neutral posts to extract and count product names using NER.
    """
    print("Loading spaCy model...")
    # Load the pre-trained English model
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Spacy model 'en_core_web_sm' not found.")
        print("Please run: python -m spacy download en_core_web_sm")
        return

    product_mentions = []
    
    print("Connecting to database and fetching posts...")
    with app.app_context():
        # Query for posts with a positive or neutral sentiment
        posts_to_analyze = RedditPost.query.filter(
            RedditPost.sentiment_label.in_(['positive', 'neutral'])
        ).all()

        if not posts_to_analyze:
            print("No positive or neutral posts found in the database.")
            return
            
        print(f"Analyzing {len(posts_to_analyze)} posts for product names...")

        # We will use the original title for NER as it has proper casing (e.g., "iPhone")
        for post in posts_to_analyze:
            doc = nlp(post.title)
            # Extract entities recognized as products or organizations
            for ent in doc.ents:
                if ent.label_ in ["PRODUCT", "ORG"]:
                    product_mentions.append(ent.text)

    if not product_mentions:
        print("No product names were identified.")
        return

    # Count the most common product mentions
    trend_counts = Counter(product_mentions)
    
    print("\n--- Top 20 Trending Products (from Positive/Neutral Posts) ---")
    for product, count in trend_counts.most_common(20):
        print(f"{product}: {count} mentions")

# Main execution block
if __name__ == '__main__':
    
    analyze_product_trends()
