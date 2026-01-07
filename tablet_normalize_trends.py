import re
import json
from collections import Counter
import os
import sys
import nltk
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# --- Flask + SQLAlchemy app for Tablets (to access the correct DB) ---
tablet_app = Flask(__name__)
tablet_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tablet_reddit_posts.db'
tablet_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
tablet_db = SQLAlchemy(tablet_app)

# Define the model to match the structure in tablet_collect_data.py
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
    extracted_tablets = tablet_db.Column(tablet_db.Text, nullable=True)

    @property
    def tablets(self):
        if self.extracted_tablets:
            try:
                return json.loads(self.extracted_tablets)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

# --- NLTK Configuration ---
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("Downloading necessary NLTK data (punkt, averaged_perceptron_tagger)...")
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)

# --- Configuration for Tablet Normalization ---
GENERIC_BRANDS = {
    "apple", "samsung", "microsoft", "lenovo", "amazon", "huawei", "xiaomi", 
    "google", "oneplus", "ipad", "surface", "galaxy", "tab", "pixel"
}
NOISY_TERMS = {
    "tablet", "pad", "pro", "air", "mini", "plus", "ultra", "go", "fe", "max",
    "pen", "pencil", "keyboard", "case", "screen", "display", "wifi", "cellular",
    "android", "ipados", "windows", "gen", "generation", "new", "used"
}
PATTERN_MAP = {
    # Apple iPads
    r"^(apple)? ?ipad ?(pro|air|mini)? ?(\d{1,2})? ?(gen|th)? ?(m1|m2|m4)?$": lambda m: f"Apple iPad {m.group(2).title() if m.group(2) else ''} {m.group(5).upper() if m.group(5) else ''}".strip(),
    r"^(apple)? ?ipad ?(\d{1,2})? ?(pro|air|mini)?$": lambda m: f"Apple iPad {m.group(3).title() if m.group(3) else ''}".strip(),
    # Samsung Galaxy Tabs
    r"^(samsung)? ?galaxy ?tab ?s ?(\d{1,2}) ?(ultra|plus|\+|fe)?$": lambda m: f"Samsung Galaxy Tab S{m.group(2)}{' ' + m.group(3).replace('+', 'Plus').upper() if m.group(3) else ''}",
    r"^(samsung)? ?galaxy ?tab ?a ?(\d{1,2}) ?(lite)?$": lambda m: f"Samsung Galaxy Tab A{m.group(2)}{' Lite' if m.group(3) else ''}",
    # Microsoft Surface
    r"^(microsoft|surface)? ?(pro|go) ?(\d)$": lambda m: f"Microsoft Surface {m.group(2).title()} {m.group(3)}",
    # Xiaomi Pad
    r"^(xiaomi|mi)? ?pad ?(\d) ?(pro)?$": lambda m: f"Xiaomi Pad {m.group(2)}{' Pro' if m.group(3) else ''}",
    # OnePlus Pad
    r"^(oneplus)? ?pad ?(go)?$": lambda m: f"OnePlus Pad{' Go' if m.group(2) else ''}",
    # Google Pixel Tablet
    r"^(google)? ?pixel ?tablet$": lambda m: "Google Pixel Tablet",
    # Lenovo Tabs
    r"^(lenovo)? ?tab ?(p\d{2}|m\d{2}) ?(pro|plus)?$": lambda m: f"Lenovo Tab {m.group(2).upper()}{' ' + m.group(3).title() if m.group(3) else ''}",
    # Amazon Fire
    r"^(amazon)? ?fire ?(hd)? ?(\d{1,2}) ?(plus|kids)?$": lambda m: f"Amazon Fire {'HD ' if m.group(2) else ''}{m.group(3)}{' ' + m.group(4).title() if m.group(4) else ''}",
}

def filter_with_nltk_pos(mentions):
    """
    Filters a list of mentions, keeping only those that are likely product names
    based on NLTK's Part-of-Speech (POS) tagging.
    """
    product_candidates = []
    VALID_TAGS = {'NNP', 'NNPS', 'NN', 'NNS', 'CD', 'FW'}

    for mention in set(mentions):
        tokens = nltk.word_tokenize(mention)
        tags = nltk.pos_tag(tokens)
        
        is_valid_product = all(tag in VALID_TAGS for word, tag in tags)
        
        if is_valid_product:
            product_candidates.append(mention)
            
    return [mention for mention in mentions if mention in product_candidates]

def normalize_tablet_list(tablet_list):
    """
    Takes a list of raw extracted tablet names and returns a cleaned, standardized list.
    """
    normalized_names = []
    for name in tablet_list:
        clean_name = name.lower().strip()
        if clean_name in GENERIC_BRANDS or clean_name in NOISY_TERMS:
            continue
        is_matched = False
        for pattern, replacement in PATTERN_MAP.items():
            match = re.fullmatch(pattern, clean_name)
            if match:
                standard_name = replacement(match) if callable(replacement) else replacement
                normalized_names.append(standard_name.strip())
                is_matched = True
                break
        if not is_matched and len(clean_name) > 3:
            normalized_names.append(name.title())
    return normalized_names

def analyze_and_print_trends():
    """
    Main function to fetch, filter, normalize, and print tablet trends.
    """
    all_extracted_tablets = []
    print("Connecting to tablet database and fetching extracted data...")
    with tablet_app.app_context():
        posts = RedditPost.query.filter(RedditPost.extracted_tablets.isnot(None)).all()
        for post in posts:
            all_extracted_tablets.extend(post.tablets)
    
    print(f"Found a total of {len(all_extracted_tablets)} raw tablet mentions to process.")

    # Step 1: NLTK Filtering
    print("\nStep 1: Filtering mentions with NLTK Part-of-Speech tagging...")
    product_candidates = filter_with_nltk_pos(all_extracted_tablets)
    print(f"--> Kept {len(product_candidates)} candidates after NLTK filtering.")
    
    # Step 2: Normalization
    print("\nStep 2: Normalizing candidates with regex and custom rules...")
    final_list = normalize_tablet_list(product_candidates)
    
    trend_counts = Counter(final_list)
    
    print("\n--- Top 20 Final Tablet Trends ---")
    print("-" * 55)
    
    if not trend_counts:
        print("No definitive product trends could be identified after cleaning.")
        return

    print(f"{'Rank':<5} | {'Tablet Model':<35} | {'Mentions'}")
    print("-" * 55)
    for i, (model, count) in enumerate(trend_counts.most_common(30), 1):
        print(f"{i:<5} | {model:<35} | {count}")

if __name__ == '__main__':
    analyze_and_print_trends()
