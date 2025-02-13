import src.scraper_module as scraper
from zenml import step, pipeline


@step
def setup_config() -> scraper.ScraperConfig:
    return scraper.load_config()


@step
def get_reddit_posts(config: scraper.ScraperConfig):
    collection = scraper.get_mongo_collection(config)
    existing_ids = {doc["post_id"] for doc in collection.find({}, {"post_id": 1})}
    reddit_instance = scraper.initialize_reddit(config)
    reddit_posts = scraper.fetch_posts(config, reddit_instance, existing_ids)
    return reddit_posts


@step
def process_reddit_posts(config: scraper.ScraperConfig, posts):
    image_data = scraper.download_images(posts, config)
    text_data = scraper.extract_text(image_data, config)

    return text_data


@step
def load_to_mongo_db(text_data, config):
    collection = scraper.get_mongo_collection(config)
    scraper.store_results(text_data, collection)


@pipeline
def scrape_reddit_posts():
    config = setup_config()
    reddit_posts = get_reddit_posts(config)
    text_data = process_reddit_posts(config, reddit_posts)
    load_to_mongo_db(text_data, config)


if __name__ == "__main__":
    scrape_reddit_posts()
