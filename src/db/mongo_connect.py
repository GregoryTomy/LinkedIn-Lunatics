from typing import List
from loguru import logger
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.scraper_entities import ProcessedPost
from src.settings import settings


class MongoDBConnector:
    _instance: MongoClient | None = None

    # Singleton design pattern
    # Ensures only one instance of the MongoDBConnector class is created throughout the application's lifecycle.
    def __new__(cls, *args, **kwargs) -> MongoClient:
        if cls._instance is None:
            try:
                cls._instance = MongoClient(
                    "localhost:27017",
                    username=settings.MONGO_USERNAME,
                    password=settings.MONGO_PASSWORD,
                    authSource=settings.MONGO_AUTH_SOURCE,
                )
            except ConnectionFailure as e:
                logger.error(f"Couldn't connect to Mongo database: {e}")

        logger.info("Successfull connection to MongoDB")

        return cls._instance


connection = MongoDBConnector()
