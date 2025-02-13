import pytest
import os

from requests.api import get
from src.scraper import get_mongo_collection, ScraperConfig, load_config
from dotenv import load_dotenv


config = load_config()


def test_mongo_connection():
    collection = get_mongo_collection(config)
    assert isinstance(collection, list), "Did not return a list of collection ids"
