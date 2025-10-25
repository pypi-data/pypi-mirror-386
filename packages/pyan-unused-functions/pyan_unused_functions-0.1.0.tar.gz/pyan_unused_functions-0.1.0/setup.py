"""
Setup configuration for pyan-unused-functions package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="pyan-unused-functions",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Find unused functions in Python codebases - perfect for CLI usage and CI/CD pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pyan-unused-functions",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pyan3==1.1.1",
    ],
    entry_points={
        "console_scripts": [
            "pyan-unused-functions=pyan_unused_functions.cli:main",
        ],
    },
    keywords="static-analysis code-quality unused-code linter ast dead-code code-cleanup ci-cd github-actions cli-tool python-analysis code-maintenance",
)
