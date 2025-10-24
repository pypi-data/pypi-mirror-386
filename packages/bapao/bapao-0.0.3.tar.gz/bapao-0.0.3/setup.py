#!/usr/bin/env python3
"""
BAPAO setup script for backwards compatibility.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="bapao",
    version="0.1.0",
    description="Developer Environment Sync Engine - Make your entire development environment portable",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="BAPAO Team",
    author_email="team@bapao.dev",
    url="https://gitlab.com/bapao/bapao-sync",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "cryptography>=3.4.0",
        "rich>=10.0.0",
        "pathlib>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ]
    },
    entry_points={
        "console_scripts": [
            "bapao=bapao.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=["development", "environment", "sync", "git", "ssh", "gpg", "devtools"],
    project_urls={
        "Bug Reports": "https://gitlab.com/bapao/bapao-sync/-/issues",
        "Source": "https://gitlab.com/bapao/bapao-sync",
        "Documentation": "https://gitlab.com/bapao/bapao-sync/-/blob/main/README.md",
    },
)