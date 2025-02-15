from typing import List
from src.scraper_entities import ProcessedPost
from src.settings import settings
from src.db.mongo_service import MongoDBService


def get_raw_documents() -> List[ProcessedPost]:
    """Get Documents from MongoDB"""
    mongo_client = MongoDBService()

    raw_documents = mongo_client.get_documents_bulk()

    return raw_documents


if __name__ == "__main__":
    doc = get_raw_documents()
    print(doc[1])
