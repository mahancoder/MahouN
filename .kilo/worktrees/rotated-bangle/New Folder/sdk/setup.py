#!/usr/bin/env python3
"""
Setup script for MAHOUN Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="mahoun-sdk",
    version="1.0.0",
    author="MAHOUN Team",
    author_email="support@mahoun.ai",
    description="Official Python SDK for MAHOUN Advanced Chunking & Vector DB API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/mahoun",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "sphinx-autodoc-typehints>=1.22.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mahoun-examples=examples:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="mahoun vector-database chunking embedding retrieval nlp legal-ai",
    project_urls={
        "Bug Reports": "https://github.com/your-org/mahoun/issues",
        "Documentation": "https://docs.mahoun.ai",
        "Source": "https://github.com/your-org/mahoun",
    },
)
