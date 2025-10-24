#!/usr/bin/env python3
"""
Setup file for Cython compilation and PyPI upload
"""

from setuptools import setup, find_packages
from Cython.Build import cythonize
from setuptools.extension import Extension
import os

# Read requirements
with open("requirements.txt", "r", encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README
with open("README.md", "r", encoding='utf-8') as f:
    long_description = f.read()

# Define extensions for Cython compilation
extensions = [
    Extension(
        "mashrur_facebook_scraper.scraper_core",
        ["mashrur_facebook_scraper/scraper_core.py"]
    ),
    Extension(
        "mashrur_facebook_scraper.simple",
        ["mashrur_facebook_scraper/simple.py"]
    )
]

setup(
    name="mashrur-facebook-scraper",
    version="2.0.4",
    author="Mashrur Rahman",
    author_email="mashrur950@gmail.com",
    description="Professional-grade Facebook data extraction tool - Cython compiled for code protection",
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
    install_requires=requirements,
    ext_modules=cythonize(extensions, build_dir="build"),
    zip_safe=False,
    include_package_data=True,
)