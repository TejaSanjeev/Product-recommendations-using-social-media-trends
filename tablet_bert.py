import os
import sys
import json
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Make sure we can import the tablet DB model
sys.path.append(os.getcwd())
try:
    from tablet_collect_data import tablet_app, tablet_db, RedditPost
except Exception:
    from tablet_collect_data import tablet_app, tablet_db, RedditPost

MODEL_NAME = "dslim/bert-base-NER"

print("Loading BERT NER model for tablet extraction... (this may take a moment)")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy=None)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    raise


def group_consecutive_entities(ner_results):
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

    cleaned = []
    for ent in grouped_entities:
        ent_fixed = ent.replace('##', '')
        ent_fixed = ent_fixed.strip()
        if ent_fixed:
            cleaned.append(ent_fixed)
    return cleaned


def extract_full_tablet_names(text: str):
    if not text or not isinstance(text, str):
        return []

    try:
        ner_results = ner_pipeline(text)
    except Exception as e:
        print(f"NER pipeline failed on text: {e}")
        return []

    full_names = group_consecutive_entities(ner_results)
    return full_names


def process_all_tablet_posts(only_missing=True):
    with tablet_app.app_context():
        if only_missing:
            posts = RedditPost.query.filter((RedditPost.extracted_tablets == None) | (RedditPost.extracted_tablets == '')).all()
        else:
            posts = RedditPost.query.all()

        if not posts:
            print("No posts found to process in tablet_reddit_posts.db.")
            return

        print(f"Processing {len(posts)} posts for tablet entity extraction...")

        updated = 0
        for post in posts:
            text = f"{post.title or ''}. {post.body or ''}"
            entities = extract_full_tablet_names(text)
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
                post.extracted_tablets = json.dumps(deduped)
                tablet_db.session.add(post)
                updated += 1
            except Exception as e:
                print(f"Failed to set extracted_tablets for post {post.id}: {e}")

        if updated:
            tablet_db.session.commit()
        print(f"Finished. Updated {updated} posts.")


if __name__ == '__main__':
    process_all_tablet_posts()
