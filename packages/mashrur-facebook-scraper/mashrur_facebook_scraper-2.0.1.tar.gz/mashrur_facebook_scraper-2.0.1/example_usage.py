#!/usr/bin/env python3
"""
Ultra Simple Example - Just 5 Parameters
Compile with: python -m nuitka --standalone --onefile example_usage.py
"""

from mashrur_facebook_scraper import scrape_facebook_posts

# Ultra simple usage - just 5 parameters
posts = scrape_facebook_posts(
    "sam.intellij.2@gmail.com",                 # Replace with your email
    "sa103940",                          # Replace with your password
    "https://www.facebook.com/indianexpress", # Replace with target page
    1,                                        # Number of posts
    "my_scraped_data.json"                    # Output filename
)

print(f"Scraped {len(posts)} posts!")
print("Data saved to: my_scraped_data.json")