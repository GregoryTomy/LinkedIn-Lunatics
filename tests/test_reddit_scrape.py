import pytest
import os
import praw
from src.scraper import (
    initialize_reddit,
    ScraperConfig,
    fetch_reddit_posts,
    load_config,
    get_mongo_collection,
)


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def reddit_instance(config):
    return initialize_reddit(config)


@pytest.fixture
def mongo_collection(config):
    return get_mongo_collection(config)


@pytest.mark.dependency()
def test_initialize_reddit(config):
    reddit = initialize_reddit(config)
    assert isinstance(reddit, praw.Reddit), (
        "Reddit instance is not initialized properly"
    )


@pytest.mark.dependency(depends=["test_initialize_reddit"])
def test_fetch_reddit_posts(config, mongo_collection, reddit_instance):
    # test with only 1 post
    config.limit = 2
    reddit_posts = fetch_reddit_posts(config, mongo_collection, reddit_instance)
    assert isinstance(reddit_posts, list), "fetch_reddit_posts should return a list"
    assert len(reddit_posts) > 0, "No posts were fetched"
