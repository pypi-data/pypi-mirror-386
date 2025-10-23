from setuptools import setup, find_packages
from pathlib import Path

# Safely read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="tabular-column-classifier",
    version="0.3.0",
    description="Fast spaCy-based column classifier with optional LLM refinement.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Roberto Avogadro",
    author_email="roberto.avogadro@sintef.no",
    url="https://github.com/roby-avo/tabular-column-classifier",
    project_urls={
        "Source": "https://github.com/roby-avo/tabular-column-classifier",
        "Issues": "https://github.com/roby-avo/tabular-column-classifier/issues",
    },
    license="Apache License 2.0",
    packages=find_packages(include=["column_classifier", "column_classifier.*"]),
    install_requires=[
        "pandas>=1.4",
        "spacy>=3.7.5",
    ],
    extras_require={
        "llm": ["ollama>=0.3.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
