from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="indolaw-scraper",
    version="0.1.2",  # versi baru
    author="Alam Mahadika",
    author_email="alam.mahadika.psm@umy.ac.id",
    description="Scraper for official Indonesian legal documents from various institutions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alammahadika/indolaw_scraper",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "beautifulsoup4>=4.9.3",
        "click>=8.0.0",
        "urllib3>=1.26.4"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
