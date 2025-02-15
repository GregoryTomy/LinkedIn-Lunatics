from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass(frozen=True)
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
    limit: int = 100
    image_dir: Path = Path("data/images")
    tesseract_config: str = "--oem 3 --psm 6 -l eng"


@dataclass(frozen=True)
class RedditPost:
    post_id: str
    title: str
    score: int
    url: str
    num_comments: int
    upvote_ratio: float


@dataclass(frozen=True)
class DownloadedPost(RedditPost):
    image_path: Path


@dataclass(frozen=True)
class ProcessedPost(DownloadedPost):
    text: Optional[str]
