from setuptools import setup, find_packages

setup(
    name='indolaw_scraper',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'beautifulsoup4>=4.9.3',
        'urllib3>=1.26.4',
        'click>=8.0.0',
    ],
    author='Alam Mahadika',
    author_email='alam.mahadika.psm@umy.ac.id',
    description='A Python package to scrape Indonesian legal documents from government websites.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Alammahadika/indolaw_scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'indolaw_scraper=indolaw_scraper.cli:main',
        ],
    },
    include_package_data=True,
    python_requires='>=3.6',
)

