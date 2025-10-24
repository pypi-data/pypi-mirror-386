"""
Setup script for EasyData package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="easydata-ds",
    version="0.1.0",
    author="Cole Ragone",
    author_email="coleragone@example.com",  # Update with your email
    description="A Python library for data scientists to easily apply functions to datasets with a terminal UI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/coleragone/easydata",  # Update with your repo URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "easydata=easydata.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "easydata": ["*.md", "*.txt"],
    },
    keywords="data science, pandas, terminal ui, data processing, decorator",
    project_urls={
        "Bug Reports": "https://github.com/coleragone/easydata/issues",
        "Source": "https://github.com/coleragone/easydata",
        "Documentation": "https://github.com/coleragone/easydata#readme",
    },
)
