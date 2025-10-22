#!/usr/bin/env python3
"""Setup script for git-hotspot-ai."""

from pathlib import Path
from setuptools import find_packages, setup

# read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")


# read version from __init__.py
def get_version():
    init_file = this_directory / "git_hotspot_ai" / "__init__.py"
    with open(init_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"


setup(
    name="git-hotspot-ai",
    version=get_version(),
    author="Your Name",
    author_email="your.email@example.com",
    description="Analyze git hotspots and trigger AI post-processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/git-hotspot-ai",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/git-hotspot-ai/issues",
        "Source": "https://github.com/yourusername/git-hotspot-ai",
    },
    packages=find_packages(),
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
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    install_requires=[
        # no external dependencies for now
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "git-hotspot-ai=git_hotspot_ai.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
