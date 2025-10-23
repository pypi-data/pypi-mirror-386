"""
Setup script for Citation Hallucination Stop library.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="citation-hallucination-stop",
    version="1.0.1",
    author="Citation Hallucination Stop Team",
    author_email="citation.hallucination.stop@example.com",
    description="A Python library for filtering academic references to match only in-text citations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/citation-hallucination-stop",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "citation-hallucination-stop=citation_hallucination_stop.cli:main",
        ],
    },
)
