#!/usr/bin/env python3
"""
Simple scraper function with 4 parameters only
"""

from .scraper_core import FacebookScraper


def scrape_facebook_posts(email, password, page_url, num_posts, output_filename):
    """
    Scrape Facebook posts - Simple Version with 5 Parameters

    Args:
        email (str): Facebook email
        password (str): Facebook password
        page_url (str): Facebook page URL
        num_posts (int): Number of posts to scrape
        output_filename (str): Output JSON filename

    Returns:
        list: Scraped posts data

    Example:
        posts = scrape_facebook_posts("email@gmail.com", "password", "https://facebook.com/page", 5, "my_data.json")
    """

    # Show clean banner
    print("========================================")
    print("    Advanced Facebook Data Extractor")
    print("        Made by Mashrur Rahman")
    print("========================================")

    scraper = None
    try:
        # Initialize and run scraper
        scraper = FacebookScraper(email, password)
        scraper.initialize_driver()
        scraper.login()
        scraper.navigate_to_profile(page_url)

        # Scrape posts with custom filename
        posts_data = scraper.scrape_posts_graphql(num_posts=num_posts, output_filename=output_filename)

        return posts_data

    finally:
        if scraper:
            try:
                scraper.close()
            except:
                pass