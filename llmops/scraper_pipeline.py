import src.scraper as scraper
from zenml import step, pipeline


@step
def setup_config() -> scraper.ScraperConfig:
    return scraper.load_config()


@step
def get_reddit_posts(config: scraper.ScraperConfig):
    collection = scraper.get_mongo_collection(config)
    reddit_instance = scraper.initialize_reddit(config)
    reddit_posts = scraper.fetch_reddit_posts(
        config,
        collection,
        reddit_instance,
    )
    return reddit_posts


@step
def process_reddit_posts(config: scraper.ScraperConfig, posts):
    image_data = scraper.download_images(posts, config)
    text_data = scraper.extract_text_from_images(image_data)

    return text_data


@step
def load_to_mongo_db(text_data, config):
    collection = scraper.get_mongo_collection(config)
    scraper.store_in_mongodb(text_data, collection)


@pipeline
def scrape_reddit_posts():
    config = setup_config()
    reddit_posts = get_reddit_posts(config)
    text_data = process_reddit_posts(config, reddit_posts)
    load_to_mongo_db(text_data, config)


if __name__ == "__main__":
    scrape_reddit_posts()
