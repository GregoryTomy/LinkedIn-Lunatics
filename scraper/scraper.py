from datetime import time
import os
import requests
from PIL import Image
from dataclasses import dataclass
from dotenv import load_dotenv

import pandas as pd
import praw
import pytesseract
from loguru import logger
from pymongo import MongoClient


@dataclass
class ScraperConfig:
    client_id: str
    clinet_secret: str
    user_agent: str
    mongo_db: str
    collection_name: str
    subreddit_name: str = "LinkedInLunatics"
    limit: int = 10000
    # output_csv: str = "data/linkedin_posts.csv"
    # image_folder: str = "data/images"
    sleep_seconds: float = 0.0


def load_config() -> ScraperConfig:
    """
    Load environment variables and return ScraperConfig dataclass
    """
    load_dotenv()
    return ScraperConfig(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        user_agent=os.getenv("USER_AGENT"),
        mongo_db=os.getenv("MONGO_DB_NAME"),
        collection_name=os.getenv("MONGO_COLLECTION"),
    )


def get_mongo_collection(config: ScraperConfig):
    """Connect to MongoDB and return the collection object."""
    client = MongoClient()


def initialize_reddit(config: ScraperConfig) -> praw.Reddit:
    """Initialize reddit instance using PRAW"""
    return praw.Reddit(
        client_id=config.client_id,
        client_secret=config.client_secret,
        user_agent=config.user_agent,
    )


def ensure_directories(config: ScraperConfig) -> None:
    """Ensures the output directories exist"""
    os.makedirs(config.image_folder, exist_ok=True)


def load_existing_post_ids(config: ScraperConfig) -> set:
    """
    Load existing post IDs from CSV, if it exists.
    Return a set of post IDs for duplicate checks.
    """
    if not os.path.exists(config.output_csv):
        return set()

    try:
        df = pd.read_csv(config.output_csv, usecols=["post_id"])
        return set(df["post_id"].astype(str).tolist())

    except Exception as e:
        logger.warning(f"Could not load existing CSV: {e}")
        return set()


def download_image(
    url: str,
    post_id: str,
    config: ScraperConfig,
) -> str:
    """
    Download image from URL. Return local file path or None if failed.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            image_path = os.path.join(config.image_folder, f"{post_id}.jpg")
            with open(image_path, "wb") as file:
                file.write(response.content)
            return image_path
        else:
            logger.warning(
                f"[{post_id}] Recieved non-200 status code: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"[Download Error] Post {post_id}: {e}")


def clean_text(text: str) -> str:
    """Clean and normalize extracted text from images"""
    if not text:
        return ""
    text = text.replace("|", "I")
    text = " ".join(text.split())  # normalize whitespace

    ui_elements = [
        "Like",
        "Comment",
        "Share",
        "Reply",
        "• 1st",
        "• 2nd",
        "• 3rd",
        "reactions",
        "comments",
        "Comment as",
        "See translation",
        "Edited",
    ]

    for element in ui_elements:
        text = text.replace(element, "")

    return text.strip()


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image using Tesseract. Return cleaned text"""
    try:
        image = Image.open(image_path)
        custom_config = r"--oem 3 --psm 6 -l eng"
        raw_text = pytesseract.image_to_string(image, config=custom_config)
        return clean_text(raw_text)
    except Exception as e:
        logger.error(f"[OCR Error] {image_path}: {e}")
        return ""


def gather_post_info(post, text: str) -> dict:
    """Construct a dictionary of relevant post fields and extracted text"""
    return {
        "post_id": post.id,
        "title": post.title,
        "score": post.score,
        "url": post.url,
        "text": text,
        "num_comments": post.num_comments,
        "upvote_ratio": post.upvote_ratio,
    }


def scrape_linkedin_posts(config: ScraperConfig) -> pd.DataFrame:
    pass
