#!/usr/bin/env python3
"""Setup script for Mantis web crawler package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="mantis-web-crawler",
    version="1.1.0",
    description="Web accessibility and UI bug detection tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mantis Team",
    author_email="",
    url="https://github.com/yourusername/mantis",  # Update with your actual GitHub URL
    project_urls={
        "Bug Reports": "https://github.com/yourusername/mantis/issues",
        "Source": "https://github.com/yourusername/mantis",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "dashboard": [
            "static/css/*.css",
            "static/js/*.js",
            "templates/*.html",
        ],
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "flask>=2.0.0",
        "flask-socketio>=5.0.0",
        "beautifulsoup4>=4.9.0",
        "aiohttp>=3.8.0",
        "asyncio-mqtt>=0.11.0",
        "requests>=2.25.0",
        "lxml>=4.6.0",
        "python-socketio[client]>=5.0.0",
        "cohere>=5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "mantis=orchestrator.cli:cli_main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    keywords="web-crawler accessibility ui-testing bug-detection playwright",
    license="MIT",
)