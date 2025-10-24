"""
Facebook Scraper - Simple Edition
Made by Mashrur Rahman
"""

try:
    from .simple import scrape_facebook_posts
except ImportError:
    # Fallback for compiled modules
    import importlib.util
    import os

    # Try to load compiled simple module
    current_dir = os.path.dirname(__file__)

    # Look for compiled simple module
    for ext in ['.pyd', '.so']:
        module_path = os.path.join(current_dir, f'simple{ext}')
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location("simple", module_path)
            if spec and spec.loader:
                simple_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(simple_module)
                scrape_facebook_posts = simple_module.scrape_facebook_posts
                break
    else:
        # Final fallback to source
        from .simple import scrape_facebook_posts

__version__ = "2.0.3"
__author__ = "Mashrur Rahman"

__all__ = ["scrape_facebook_posts"]