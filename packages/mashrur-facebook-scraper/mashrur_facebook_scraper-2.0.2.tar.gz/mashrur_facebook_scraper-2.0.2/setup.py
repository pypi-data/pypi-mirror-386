#!/usr/bin/env python3

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="mashrur-facebook-scraper",
    version="2.0.1",
    author="Mashrur Rahman",
    author_email="mashrur950@gmail.com",
    description="Professional-grade Facebook data extraction tool with Nuitka compilation support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mashrur/facebook-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "License :: Other/Proprietary License",
    ],
    python_requires=">=3.7",
    install_requires=[
        "selenium>=4.0.0",
        "beautifulsoup4>=4.9.0",
        "Pillow>=8.0.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "compilation": ["nuitka>=1.8.0"],
    },
    keywords="facebook scraper data-extraction social-media nuitka compiled",
    project_urls={
        "Bug Reports": "https://github.com/mashrur/facebook-scraper/issues",
        "Source": "https://github.com/mashrur/facebook-scraper",
        "Documentation": "https://docs.mashrur-scraper.com",
    },
)