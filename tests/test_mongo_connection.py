import pytest
import os

from requests.api import get
from src.scraper import get_mongo_collection, ScraperConfig, load_config
from dotenv import load_dotenv


config = load_config()


def test_mongo_connection():
    collection = get_mongo_collection(config)

    try:
        _ = collection.estimated_document_count()
        assert True
    except Exception as e:
        pytest.fail(f"MongoDB conection failed: {e}")
