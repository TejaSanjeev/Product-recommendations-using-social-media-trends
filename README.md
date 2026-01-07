# Create the virtual environment (named 'venv')
python -m venv venv


# To activate the environment
.\venv\Scripts\activate

# To install packages
pip install Flask
pip install Flask-SQLAlchemy
pip install praw
pip install pandas praw nltk

# to download plunkt_tab
enter "python"
import nltk
nltk.download('punkt_tab')

# To run the server
flask --app app run

# To collect the dataset
python collect_data.py






reddit = praw.Reddit(
    client_id="",
    client_secret="",
    user_agent="",
    username="",
    password="",
)
print("Successfully authenticated with Reddit.")

# --- 2. Data Fetching ---
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