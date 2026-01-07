import re
import json
from collections import Counter
import os
import sys
import nltk
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# --- Flask + SQLAlchemy app for Laptops (to access the correct DB) ---
# This setup mirrors the one in laptop_collect_data.py
laptop_app = Flask(__name__)
laptop_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laptop_reddit_posts.db'
laptop_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
laptop_db = SQLAlchemy(laptop_app)

# Define the model to match the structure in laptop_collect_data.py
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
    extracted_laptops = laptop_db.Column(laptop_db.Text, nullable=True)

    @property
    def laptops(self):
        if self.extracted_laptops:
            try:
                return json.loads(self.extracted_laptops)
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

# --- Configuration for Laptop Normalization ---
GENERIC_BRANDS = {
    "apple", "dell", "hp", "lenovo", "asus", "acer", "msi", "razer", "samsung", 
    "microsoft", "huawei", "lg", "google", "macbook", "thinkpad", "surface",
    "mac", "alienware", "xps", "spectre", "omen", "legion", "yoga", "zenbook",
    "rog", "tuf", "predator", "nitro", "swift", "inspiron", "pavilion", "ideapad"
}
NOISY_TERMS = {
    "laptop", "notebook", "pc", "windows", "macos", "linux", "intel", "amd", "ryzen", 
    "nvidia", "geforce", "rtx", "gtx", "ram", "ssd", "hdd", "screen", "display", 
    "keyboard", "trackpad", "usb", "thunderbolt", "wifi", "bluetooth", "gaming", 
    "pro", "air", "book", "ultra", "slim", "oled", "touchscreen", "convertible",
    "i3", "i5", "i7", "i9", "gen", "edition", "new", "used", "refurbished","Amazon","Usbc"
}
PATTERN_MAP = {
    # Apple MacBooks
    r"^(apple|macbook)? ?(pro|air) ?(m1|m2|m3)? ?(\d{2})? ?(inch|\")?$": lambda m: f"Apple MacBook {m.group(2).title()}{' ' + m.group(3).upper() if m.group(3) else ''}",
    r"^(macbook) (\d{2}) ?(inch|\")?$": lambda m: "Apple MacBook",
    # Dell
    r"^(dell)? ?xps ?(\d{2}) ?(\d{4})?$": lambda m: f"Dell XPS {m.group(2)}",
    r"^(dell)? ?inspiron ?(\d{2}) ?(\d{4})?$": lambda m: f"Dell Inspiron {m.group(2)}",
    r"^(dell|alienware)? ?(m|x)(\d{2}) ?(r\d)?$": lambda m: f"Alienware {m.group(2).upper()}{m.group(3)}",
    # HP
    r"^(hp)? ?spectre ?x360 ?(\d{2})?$": lambda m: f"HP Spectre x360 {m.group(2) if m.group(2) else ''}".strip(),
    r"^(hp)? ?envy ?x360 ?(\d{2})?$": lambda m: f"HP Envy x360 {m.group(2) if m.group(2) else ''}".strip(),
    r"^(hp)? ?omen ?(\d{2}|\d{2}l)?$": lambda m: f"HP Omen {m.group(2) if m.group(2) else ''}".strip(),
    # Lenovo
    r"^(lenovo)? ?thinkpad ?(x1|t\d{2,3}|p\d{2}) ?(carbon|yoga|nano)?$": lambda m: f"Lenovo ThinkPad {m.group(2).upper()}{' ' + m.group(3).title() if m.group(3) else ''}",
    r"^(lenovo)? ?legion ?(pro|slim)? ?(5|7|9)i?$": lambda m: f"Lenovo Legion{' ' + m.group(2).title() if m.group(2) else ''} {m.group(3)}",
    r"^(lenovo)? ?yoga ?(slim|book)? ?(\d{1,2})i?$": lambda m: f"Lenovo Yoga{' ' + m.group(2).title() if m.group(2) else ''} {m.group(3)}",
    # ASUS
    r"^(asus)? ?(rog|republic of gamers)? ?(zephyrus|strix|flow) ?([a-z]{1,2}\d{2})?$": lambda m: f"ASUS ROG {m.group(3).title()} {m.group(4).upper() if m.group(4) else ''}".strip(),
    r"^(asus)? ?zenbook ?(duo|flip|pro)? ?(\d{2})?$": lambda m: f"ASUS ZenBook{' ' + m.group(2).title() if m.group(2) else ''} {m.group(3) if m.group(3) else ''}".strip(),
    r"^(asus)? ?tuf ?(gaming|dash) ?([af]\d{2})?$": lambda m: f"ASUS TUF Gaming {m.group(3).upper() if m.group(3) else ''}".strip(),
    # Acer
    r"^(acer)? ?predator ?(helios|triton) ?(\d{3})?$": lambda m: f"Acer Predator {m.group(2).title()} {m.group(3) if m.group(3) else ''}".strip(),
    r"^(acer)? ?nitro ?(5|v)?$": lambda m: f"Acer Nitro {m.group(2) if m.group(2) else '5'}",
    r"^(acer)? ?swift ?(x|go|edge|\d)?$": lambda m: f"Acer Swift {m.group(2).upper() if m.group(2) else ''}".strip(),
    # Microsoft Surface
    r"^(microsoft|surface)? ?(pro|laptop|book|go|studio) ?(\d)?$": lambda m: f"Microsoft Surface {m.group(2).title()} {m.group(3) if m.group(3) else ''}".strip(),
    # Razer
    r"^(razer)? ?blade ?(stealth|advanced)? ?(\d{2})?$": lambda m: f"Razer Blade {m.group(3) if m.group(3) else ''}{' ' + m.group(2).title() if m.group(2) else ''}".strip(),
}

def filter_with_nltk_pos(mentions):
    """
    Filters a list of mentions, keeping only those that are likely product names
    based on NLTK's Part-of-Speech (POS) tagging.
    """
    product_candidates = []
    VALID_TAGS = {'NNP', 'NNPS', 'NN', 'NNS', 'CD', 'FW'} # Added FW for foreign words/model numbers

    for mention in set(mentions):
        tokens = nltk.word_tokenize(mention)
        tags = nltk.pos_tag(tokens)
        
        is_valid_product = all(tag in VALID_TAGS for word, tag in tags)
        
        if is_valid_product:
            product_candidates.append(mention)
            
    return [mention for mention in mentions if mention in product_candidates]

def normalize_laptop_list(laptop_list):
    """
    Takes a list of raw extracted laptop names and returns a cleaned, standardized list.
    """
    normalized_names = []
    for name in laptop_list:
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
            # Basic title case for unmatched items as a fallback
            normalized_names.append(name.title())
    return normalized_names

def analyze_and_print_trends():
    """
    Main function to fetch, filter, normalize, and print laptop trends.
    """
    all_extracted_laptops = []
    print("Connecting to laptop database and fetching extracted data...")
    with laptop_app.app_context():
        # Query the RedditPost model from the laptop database
        posts = RedditPost.query.filter(RedditPost.extracted_laptops.isnot(None)).all()
        for post in posts:
            # The property is named 'laptops' in the model
            all_extracted_laptops.extend(post.laptops)
    
    print(f"Found a total of {len(all_extracted_laptops)} raw laptop mentions to process.")

    # Step 1: NLTK Filtering
    print("\nStep 1: Filtering mentions with NLTK Part-of-Speech tagging...")
    product_candidates = filter_with_nltk_pos(all_extracted_laptops)
    print(f"--> Kept {len(product_candidates)} candidates after NLTK filtering.")
    
    # Step 2: Normalization
    print("\nStep 2: Normalizing candidates with regex and custom rules...")
    final_list = normalize_laptop_list(product_candidates)
    
    trend_counts = Counter(final_list)
    
    print("\n--- Top 20 Final Laptop Trends ---")
    print("-" * 55)
    
    if not trend_counts:
        print("No definitive product trends could be identified after cleaning.")
        return

    print(f"{'Rank':<5} | {'Laptop Model':<35} | {'Mentions'}")
    print("-" * 55)
    for i, (model, count) in enumerate(trend_counts.most_common(30), 1):
        print(f"{i:<5} | {model:<35} | {count}")

if __name__ == '__main__':
    analyze_and_print_trends()
