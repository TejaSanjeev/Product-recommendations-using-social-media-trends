import re
import json
from collections import Counter
import os
import sys
import nltk

# Ensure the script can find your Flask 'app' module
sys.path.append(os.getcwd())
from app import app, db, RedditPost

# --- NLTK Configuration ---
# Download necessary NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    print("Downloading necessary NLTK data (punkt, averaged_perceptron_tagger)...")
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')

# --- Configuration for Normalization (No Changes Here) ---
GENERIC_BRANDS = {
    "apple", "samsung", "google", "xiaomi", "oneplus", "realme", "motorola",
    "asus", "honor", "oppo", "vivo", "nothing", "pixel", "galaxy", "xiao", 
    "one", "onep","iphone", "redmi", "poco", "moto", "infinix", "rog", "zenfone",
    "india","china","gemini","reddit",
}
NOISY_TERMS = {
    "ultra", "pro", "max", "plus", "lite", "edge", "red", "chinese", "cheap",
    "ios", "windows", "android", "usb", "bluetooth", "whatsapp", "youtube", 
    "amazon", "camera", "battery", "screen", "s24", "s25","Usa"," Europe","Canada","Usbc"," Verizon","Nfc"
}
PATTERN_MAP = {
    # This comprehensive map remains unchanged
    r"^(samsung)? ?galaxy ?s ?(\d{2}) ?(ultra|plus|\+)?$": lambda m: f"Samsung Galaxy S{m.group(2)}{' ' + m.group(3).replace('+', 'Plus').title() if m.group(3) else ''}",
    r"^(samsung)? ?galaxy ?z ?(flip|fold) ?(\d)$": lambda m: f"Samsung Galaxy Z {m.group(2).title()} {m.group(3)}",
    r"^(samsung)? ?galaxy ?a ?(\d{2})s?$": lambda m: f"Samsung Galaxy A{m.group(2)}",
    r"^(samsung)? ?galaxy ?(m|f) ?(\d{2})$": lambda m: f"Samsung Galaxy {m.group(2).upper()}{m.group(3)}",
    r"^(iphone|apple)? ?(\d{1,2}) ?(pro|plus|max|se|mini)? ?(max)?$": lambda m: f"iPhone {m.group(2)}{' ' + m.group(3).title() if m.group(3) else ''}{' Max' if m.group(4) else ''}",
    r"^(iphone|apple)? ?se ?(\d{1,2})?$": lambda m: f"iPhone SE{ ' ' + m.group(2) if m.group(2) else ''}",
    r"^(google)? ?pixel ?(\d{1,2}) ?(pro|a|xl)?$": lambda m: f"Google Pixel {m.group(2)}{' ' + m.group(3).title() if m.group(3) else ''}",
    r"^(google)? ?pixel ?fold ?(\d)?$": lambda m: f"Google Pixel Fold{ ' ' + m.group(2) if m.group(2) else ''}",
    r"^(oneplus|one ?plus) ?(\d{1,2}) ?(pro|t|r)?$": lambda m: f"OnePlus {m.group(2)}{' ' + m.group(3).title() if m.group(3) else ''}",
    r"^(oneplus|one ?plus) ?nord ?(ce)? ?(\d)? ?(lite)?$": lambda m: f"OnePlus Nord{' CE' if m.group(2) else ''}{' ' + m.group(3) if m.group(3) else ''}{' Lite' if m.group(4) else ''}",
    r"^(xiaomi|mi) ?(\d{1,2}) ?(pro|t|ultra|lite)?$": lambda m: f"Xiaomi {m.group(2)}{' ' + m.group(3).title() if m.group(3) else ''}",
    r"^redmi ?note ?(\d{1,2}) ?(pro|plus|\+)?$": lambda m: f"Redmi Note {m.group(1)}{' ' + m.group(2).replace('+', 'Plus').title() if m.group(2) else ''}",
    r"^poco ?([fmx]) ?(\d) ?(pro|gt)?$": lambda m: f"POCO {m.group(1).upper()}{m.group(2)}{' ' + m.group(3).title() if m.group(3) else ''}",
    r"^realme ?(\d{1,2}|gt) ?(pro|neo|master)? ?(\d)?$": lambda m: f"Realme {m.group(1)}{' ' + m.group(2).title() if m.group(2) else ''}{' ' + m.group(3) if m.group(3) else ''}",
    r"^oppo ?(reno|find) ?([x\d]{1,2}) ?(pro)?$": lambda m: f"OPPO {m.group(1).title()} {m.group(2)}{' Pro' if m.group(3) else ''}",
    r"^vivo ?([vx]) ?(\d{2,3}) ?(pro)?$": lambda m: f"Vivo {m.group(1).upper()}{m.group(2)}{' Pro' if m.group(3) else ''}",
    r"^(motorola|moto) ?(edge|g) ?(\d{2,3}) ?(pro|plus|fusion|power)?$": lambda m: f"Motorola {m.group(2).title()} {m.group(3)}{' ' + m.group(4).title() if m.group(4) else ''}",
    r"^(nothing)? ?phone ?\(?(\d)a?\)?$": lambda m: f"Nothing Phone ({m.group(2)})",
    r"^infinix ?(note|zero|hot) ?(\d{1,2}) ?(pro|ultra|play)?$": lambda m: f"Infinix {m.group(1).title()} {m.group(2)}{' ' + m.group(3).title() if m.group(3) else ''}",
    r"^asus ?(rog|zenfone) ?(phone)? ?(\d{1,2}) ?(pro|ultimate)?$": lambda m: f"ASUS {m.group(1).upper()} Phone {m.group(3)}{' ' + m.group(4).title() if m.group(4) else ''}",
}

# --- New NLTK Filtering Function ---
def filter_with_nltk_pos(mentions):
    """
    Filters a list of mentions, keeping only those that are likely product names
    based on NLTK's Part-of-Speech (POS) tagging.
    """
    product_candidates = []
    # Define valid POS tags for product names (Proper Noun, Noun, Cardinal Number)
    VALID_TAGS = {'NNP', 'NNPS', 'NN', 'NNS', 'CD'}

    for mention in set(mentions): # Process unique mentions for efficiency
        tokens = nltk.word_tokenize(mention)
        tags = nltk.pos_tag(tokens)
        
        # Keep the mention if all of its tokens are valid tags
        is_valid_product = all(tag in VALID_TAGS for word, tag in tags)
        
        if is_valid_product:
            product_candidates.append(mention)
            
    # Return a list containing only the mentions that passed the POS check
    return [mention for mention in mentions if mention in product_candidates]


def normalize_phone_list(phone_list):
    """
    Takes a list of raw extracted names and returns a cleaned, standardized list.
    """
    normalized_names = []
    for name in phone_list:
        clean_name = name.lower().strip()
        if clean_name in GENERIC_BRANDS or clean_name in NOISY_TERMS:
            continue
        is_matched = False
        for pattern, replacement in PATTERN_MAP.items():
            match = re.fullmatch(pattern, clean_name)
            if match:
                standard_name = replacement(match) if callable(replacement) else replacement
                normalized_names.append(standard_name)
                is_matched = True
                break
        if not is_matched and len(clean_name) > 2:
            normalized_names.append(name.title())
    return normalized_names

def analyze_and_print_trends():
    """
    Main function to fetch, filter with NLTK, normalize, and print trends.
    """
    all_extracted_phones = []
    print("Connecting to database and fetching extracted data...")
    with app.app_context():
        posts = RedditPost.query.filter(RedditPost.extracted_phones.isnot(None)).all()
        for post in posts:
            try:
                all_extracted_phones.extend(post.phones)
            except (json.JSONDecodeError, TypeError):
                continue
    
    print(f"Found a total of {len(all_extracted_phones)} raw mentions to process.")

    # --- NEW NLTK FILTERING STEP ---
    print("\nStep 1: Filtering mentions with NLTK Part-of-Speech tagging...")
    product_candidates = filter_with_nltk_pos(all_extracted_phones)
    print(f"--> Kept {len(product_candidates)} candidates after NLTK filtering.")
    
    # --- NORMALIZATION STEP (now runs on the NLTK-filtered list) ---
    print("\nStep 2: Normalizing candidates with regex and custom rules...")
    final_list = normalize_phone_list(product_candidates)
    
    trend_counts = Counter(final_list)
    
    print("\n--- Top 20 Final Smartphone Trends ---")
    print("-" * 55)
    
    if not trend_counts:
        print("No definitive product trends could be identified after cleaning.")
        return

    print(f"{'Rank':<5} | {'Smartphone Model':<35} | {'Mentions'}")
    print("-" * 55)
    for i, (model, count) in enumerate(trend_counts.most_common(30), 1):
        print(f"{i:<5} | {model:<35} | {count}")

# --- Main execution block ---
if __name__ == '__main__':
    analyze_and_print_trends()
