import os
import requests
import pytesseract
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from pymongo import MongoClient
import praw
from tqdm import tqdm
from zenml import pipeline, step
from dataclasses import dataclass
from loguru import logger


MONGO_AUTH_SOURCE = os.getenv("MONGO_AUTH_SOURCE")
MONGO_USERNAME = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")


@dataclass
class ScraperConfig:
    client_id: str
    client_secret: str
    user_agent: str
    mongo_database: str
    collection_name: str
    mongo_username: str
    mongo_password: str
    mongo_authSource: str
    subreddit_name: str = "LinkedInLunatics"
    limit: int = 2
    sleep_seconds: float = 0.0


def load_config() -> ScraperConfig:
    load_dotenv()
    return ScraperConfig(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT"),
        mongo_database=os.getenv("MONGO_DB_NAME"),
        collection_name=os.getenv("MONGO_COLLECTION"),
        mongo_username=os.getenv("MONGO_USERNAME"),
        mongo_password=os.getenv("MONGO_PASSWORD"),
        mongo_authSource=os.getenv("MONGO_AUTH_SOURCE"),
    )


def get_mongo_collection(config: ScraperConfig):
    client = MongoClient(
        "localhost:27017",
        username=config.mongo_username,
        password=config.mongo_password,
        authSource=config.mongo_authSource,
    )
    database = client[config.mongo_database]
    return database[config.collection_name]


def initialize_reddit(config: ScraperConfig) -> praw.Reddit:
    reddit = praw.Reddit(
        client_id=config.client_id,
        client_secret=config.client_secret,
        user_agent=config.user_agent,
    )

    return reddit


def fetch_reddit_posts(config: ScraperConfig, collection, reddit: praw.Reddit):
    subreddit = reddit.subreddit(config.subreddit_name)

    existing_posts = set(doc["post_id"] for doc in collection.find({}, {"post_id": 1}))
    logger.info(f"Skipping {len(existing_posts)} existing posts...")

    posts = []
    for post in subreddit.hot(limit=config.limit):
        if (
            hasattr(post, "url")
            and post.url.lower().endswith((".jpg", ".jpeg", ".png"))
            and post.id not in existing_posts
        ):
            posts.append(
                {
                    "post_id": post.id,
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "num_comments": post.num_comments,
                    "upvote_ratio": post.upvote_ratio,
                }
            )

    return posts


def download_images(posts: list, config: ScraperConfig):
    downloaded_images = []

    for post in tqdm(posts, desc="Downloading Images"):
        try:
            response = requests.get(post["url"], timeout=10)
            if response.status_code == 200:
                image_bytes = BytesIO(response.content)
                post["image_bytes"] = image_bytes
                downloaded_images.append(post)
        except Exception as e:
            print(f"Failed to download image {post['post_id']}: {e}")

    return downloaded_images


def extract_text_from_images(posts: list[dict]) -> list[dict]:
    extracted_data = []
    for post in tqdm(posts, desc="Extracting Text"):
        try:
            image = Image.open(post["image_bytes"])
            text = pytesseract.image_to_string(
                image, config="--oem 3 --psm 6 -l eng"
            ).strip()
            post["text"] = text
            extracted_data.append(post)
        except Exception as e:
            print(f"Error processing {post['image_path']}: {e}")

    return extracted_data


def store_in_mongodb(posts: list, collection):
    for post in tqdm(posts, desc="Storing in MongoDB"):
        if post.get("text") and len(post["text"]) > 50:
            try:
                collection.insert_one(post)
            except Exception as e:
                print(f"Error inserting into MongoDB: {e}")
