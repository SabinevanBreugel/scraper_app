import argparse
from functions.scraper_classes import scraper_classes 

def run_scraper(name: str, env: str, headless: bool):
    scraper_class = scraper_classes.get(name)
    print(scraper_class)
    if not scraper_class:
        raise ValueError(f"Scraper {name} is unknown.")
    scraper = scraper_class(env=env, headless=headless)
    scraper.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a scraper")
    parser.add_argument("--scraper_name", default="vacancy", help="Name of the scraper as defined in scraper_classes")
    parser.add_argument("--env", default="dev", choices=["dev", "develop", "prod"], help="Environment, if prod is chosen we use the remote webdriver")
    parser.add_argument("--headless", type=lambda x: x.lower() == "true", default=False, help="Run browser in headless mode")

    args = parser.parse_args()
    
    run_scraper(name=args.scraper_name, env=args.env, headless=args.headless)