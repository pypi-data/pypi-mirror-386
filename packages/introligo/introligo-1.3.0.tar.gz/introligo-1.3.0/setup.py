#!/usr/bin/env python
"""
Setup script for Introligo.

This file is provided for backwards compatibility.
Modern installations should use pyproject.toml.
"""

from setuptools import setup  # type: ignore[import-untyped]

# Read the long description from README
with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="introligo",
    # Version is managed by setuptools_scm from git tags (see pyproject.toml)
    author="Jakub Brzezowski",
    author_email="brzezoo@gmail.com",
    description="YAML to reStructuredText documentation generator for Sphinx",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JakubBrzezo/introligo",
    packages=["introligo"],
    package_data={
        "introligo": ["templates/*.jinja2"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Documentation",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup :: reStructuredText",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyYAML>=6.0",
        "Jinja2>=3.0",
    ],
    extras_require={
        "docs": [
            "sphinx>=4.0",
            "furo>=2023.3.27",
        ],
        "cpp": [
            "breathe>=4.0",
        ],
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "introligo=introligo:main",
        ],
    },
    keywords="documentation sphinx rst yaml generator doxygen breathe",
)
