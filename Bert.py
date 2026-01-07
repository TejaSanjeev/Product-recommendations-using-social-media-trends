import os
import sys
import json
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Ensure the script can find your Flask 'app' module
sys.path.append(os.getcwd())
from app import app, db, RedditPost

MODEL_NAME = "dslim/bert-base-NER"

print("Loading BERT NER model... (this may take a moment)")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
    # **KEY CHANGE**: We set aggregation_strategy=None to get token-level details
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy=None)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

def group_consecutive_entities(ner_results):
    """
    Intelligently groups adjacent tokens that are part of the same entity.
    For example: [('Google', 'B-ORG'), ('Pixel', 'I-ORG')] becomes "GooglePixel".
    """
    grouped_entities = []
    current_entity_words = []
    
    for token in ner_results:
        entity_label = token['entity']
        word = token['word']

        if entity_label.startswith('B-'): # Start of a new entity
            if current_entity_words:
                grouped_entities.append("".join(current_entity_words).replace('##', ''))
            current_entity_words = [word]
        elif entity_label.startswith('I-'): # Inside an entity, continue it
            if current_entity_words:
                current_entity_words.append(word)
        else: # Outside an entity, so end the current one
            if current_entity_words:
                grouped_entities.append("".join(current_entity_words).replace('##', ''))
            current_entity_words = []
            
    # Add any leftover entity at the end of the text
    if current_entity_words:
        grouped_entities.append("".join(current_entity_words).replace('##', ''))
        
    return grouped_entities

def extract_full_phone_names(text: str):
    """
    Runs the NER pipeline and uses the grouping logic to get full entity names.
    """
    if not text or not isinstance(text, str):
        return []
    
    ner_results = ner_pipeline(text)
    full_names = group_consecutive_entities(ner_results)
    return full_names

def process_all_posts():
    """Processes all posts in the database to extract full phone names."""
    with app.app_context():
        posts = RedditPost.query.all()
        if not posts:
            print("No posts found in the database.")
            return

        print(f"Re-processing {len(posts)} total posts with improved extraction...")

        for post in posts:
            full_text = f"{post.title}. {post.body or ''}"
            # Use the new function to get complete names
            phones = extract_full_phone_names(full_text)
            post.extracted_phones = json.dumps(phones)
            db.session.add(post)

        db.session.commit()
        print(f"Successfully re-processed and updated {len(posts)} posts.")

if __name__ == "__main__":
    process_all_posts()
