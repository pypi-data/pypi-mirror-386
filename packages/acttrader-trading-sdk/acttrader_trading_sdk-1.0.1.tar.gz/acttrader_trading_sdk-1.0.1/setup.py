#!/usr/bin/env python3
"""
ActTrader Python SDK
Official Python SDK for ActTrader Trading API
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Official Python SDK for ActTrader Trading API"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="acttrader-trading-sdk",
    version="1.0.1",
    description="Official Python SDK for ActTrader Trading API",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Act",
    author_email="support@acttrader.com",
    url="https://github.com/acttrader/python-trading-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    keywords=[
        "acttrader",
        "trading",
        "forex",
        "api",
        "sdk",
        "trading-api",
        "market-data",
        "websocket",
        "financial",
        "broker",
    ],
    project_urls={
        "Homepage": "https://github.com/acttrader/python-sdk",
        "Bug Reports": "https://github.com/acttrader/python-sdk/issues",
        "Source": "https://github.com/acttrader/python-sdk",
        "Documentation": "https://github.com/acttrader/python-sdk#readme",
    },
)
