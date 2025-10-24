"""
Setup script for nnez package.

This file is primarily for backwards compatibility with older pip versions.
The main configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="nnez",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Neural Network Easy Extraction - Simple LLM activation extraction in one line",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nnez",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/nnez/issues",
        "Source": "https://github.com/yourusername/nnez",
        "Documentation": "https://nnez.readthedocs.io/",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="llm, transformers, activation-extraction, interpretability, neural-networks",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*", "docs", "docs.*"]),
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.9.0",
        "transformers>=4.20.0",
        "nnsight>=0.2.0",
        "numpy>=1.19.0",
        "inflect>=6.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.17.0",
        ],
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.18.0",
        ],
        "examples": [
            "scipy>=1.7.0",
            "matplotlib>=3.4.0",
            "seaborn>=0.11.0",
            "jupyter>=1.0.0",
            "ipywidgets>=7.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # You could add CLI commands here if needed
            # "nnez=nnez.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "nnez": ["py.typed"],
    },
    zip_safe=False,
)