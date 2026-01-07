import os
import sys
import json
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Make sure we can import the laptop DB model
sys.path.append(os.getcwd())
try:
    from laptop_collect_data import laptop_app, laptop_db, RedditPost
except Exception:
    # Fallback if module path differs
    from laptop_collect_data import laptop_app, laptop_db, RedditPost

MODEL_NAME = "dslim/bert-base-NER"

print("Loading BERT NER model for laptop extraction... (this may take a moment)")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy=None)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    raise


def group_consecutive_entities(ner_results):
    """
    Groups adjacent tokens that are part of the same entity according to B-/I- tags.
    Removes WordPiece markers (##) and returns human-readable entity strings.
    """
    grouped_entities = []
    current_entity_words = []

    for token in ner_results:
        entity_label = token.get('entity', '')
        word = token.get('word', '')

        if entity_label.startswith('B-'):
            if current_entity_words:
                grouped_entities.append("".join(current_entity_words).replace('##', ''))
            current_entity_words = [word]
        elif entity_label.startswith('I-'):
            if current_entity_words:
                current_entity_words.append(word)
        else:
            if current_entity_words:
                grouped_entities.append("".join(current_entity_words).replace('##', ''))
            current_entity_words = []

    if current_entity_words:
        grouped_entities.append("".join(current_entity_words).replace('##', ''))

    # Post-process: convert wordpieces to readable words and remove empty entries
    cleaned = []
    for ent in grouped_entities:
        # If ent contains wordpiece joins (##), add spaces before capitalized sequences where appropriate
        ent_fixed = ent.replace('##', '')
        # Normalize spacing between camelcased tokens by inserting space before uppercase following lowercase
        # But keep most as-is to preserve model outputs like 'MacBook Air'
        ent_fixed = ent_fixed.strip()
        if ent_fixed:
            cleaned.append(ent_fixed)
    return cleaned


def extract_full_laptop_names(text: str):
    """
    Runs the NER pipeline and returns grouped entity names found in the input text.
    """
    if not text or not isinstance(text, str):
        return []

    try:
        ner_results = ner_pipeline(text)
    except Exception as e:
        print(f"NER pipeline failed on text: {e}")
        return []

    full_names = group_consecutive_entities(ner_results)
    return full_names


def process_all_laptop_posts(only_missing=True):
    """
    Processes posts in the laptop DB and fills `extracted_laptops` with a JSON list
    of extracted entity strings. If `only_missing` is True, only updates posts where
    `extracted_laptops` is None or empty.
    """
    with laptop_app.app_context():
        if only_missing:
            posts = RedditPost.query.filter((RedditPost.extracted_laptops == None) | (RedditPost.extracted_laptops == '')).all()
        else:
            posts = RedditPost.query.all()

        if not posts:
            print("No posts found to process in laptop_reddit_posts.db.")
            return

        print(f"Processing {len(posts)} posts for laptop entity extraction...")

        updated = 0
        for post in posts:
            text = f"{post.title or ''}. {post.body or ''}"
            entities = extract_full_laptop_names(text)
            # Optionally deduplicate while preserving order
            seen = set()
            deduped = []
            for e in entities:
                e_clean = e.strip()
                if not e_clean:
                    continue
                if e_clean not in seen:
                    seen.add(e_clean)
                    deduped.append(e_clean)

            try:
                post.extracted_laptops = json.dumps(deduped)
                laptop_db.session.add(post)
                updated += 1
            except Exception as e:
                print(f"Failed to set extracted_laptops for post {post.id}: {e}")

        if updated:
            laptop_db.session.commit()
        print(f"Finished. Updated {updated} posts.")


if __name__ == '__main__':
    process_all_laptop_posts()
