import os
from io import BytesIO
from dataclasses import dataclass, asdict, replace
from typing import Optional, List, Set
from pathlib import Path

import requests
import pytesseract
import praw
from PIL import Image
from pymongo import MongoClient
from tqdm import tqdm
from loguru import logger
from dotenv import load_dotenv

from src.scraper_entities import (
    ScraperConfig,
    DownloadedPost,
    ProcessedPost,
    RedditPost,
)


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
        image_dir=Path(os.getenv("IMAGE_DIR", "data/images")),
    )


def get_mongo_collection(config: ScraperConfig):
    client = MongoClient(
        "localhost:27017",
        username=config.mongo_username,
        password=config.mongo_password,
        authSource=config.mongo_authSource,
    )
    return client[config.mongo_database][config.collection_name]


def initialize_reddit(config: ScraperConfig) -> praw.Reddit:
    return praw.Reddit(
        client_id=config.client_id,
        client_secret=config.client_secret,
        user_agent=config.user_agent,
    )


def fetch_posts(
    config: ScraperConfig, reddit: praw.Reddit, existing_ids: Set[str]
) -> List[RedditPost]:
    subreddit = reddit.subreddit(config.subreddit_name)
    posts = []

    for submission in subreddit.hot(limit=config.limit):
        if submission.id not in existing_ids and submission.url.lower().endswith(
            (".jpg", ".jpeg", ".png")
        ):
            posts.append(
                RedditPost(
                    post_id=submission.id,
                    title=submission.title,
                    score=submission.score,
                    url=submission.url,
                    num_comments=submission.num_comments,
                    upvote_ratio=submission.upvote_ratio,
                )
            )
    return posts


def download_images(
    posts: List[RedditPost], config: ScraperConfig
) -> List[DownloadedPost]:
    config.image_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for post in tqdm(posts, desc="Downloading images"):
        try:
            response = requests.get(post.url, timeout=10)
            if response.status_code == 200:
                image_path = config.image_dir / f"{post.post_id}.jpeg"
                image_path.write_bytes(response.content)
                downloaded.append(
                    DownloadedPost(**asdict(post), image_path=str(image_path))
                )
        except Exception as e:
            logger.error(f"Failed to download {post.post_id}: {e}")

    return downloaded


def extract_text(
    posts: List[DownloadedPost], config: ScraperConfig
) -> List[ProcessedPost]:
    processed = []

    for post in tqdm(posts, desc="Extracting text"):
        try:
            with Image.open(post.image_path) as img:
                text = pytesseract.image_to_string(
                    img, config=config.tesseract_config
                ).strip()
                processed_post = ProcessedPost(**asdict(post), text=text)
                processed.append(processed_post)
        except Exception as e:
            logger.error(f"Failed OCR for {post.post_id}: {e}")

    return processed


def store_results(posts: List[ProcessedPost], collection) -> None:
    for post in tqdm(posts, desc="Storing results"):
        if post.text and len(post.text) > 50:
            try:
                collection.insert_one(asdict(post))
            except Exception as e:
                logger.error(f"Failed to store {post.post_id}: {e}")
