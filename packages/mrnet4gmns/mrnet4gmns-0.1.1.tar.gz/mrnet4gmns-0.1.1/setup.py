# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Created Date: 10/24/2025
# Author: Yajun Liu
# Contact Info: yajun.liu@asu.edu

"""
Setup script for mrnet4gmns package.
This file is kept for backward compatibility.
The main configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages

# Read the long description from README
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A multi-resolution network builder for GMNS networks"

setup(
    name="mrnet4gmns",
    version="0.1.1",
    author="Yajun Liu",
    author_email="leo@asu.edu",
    description="A multi-resolution network builder for GMNS networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://pypi.org/project/mrnet4gmns/",
    packages=find_packages(include=['mrnet4gmns', 'mrnet4gmns.*']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "shapely>=2.0.0",
        "geopandas>=0.10.0",
        "networkx>=2.6.0",
        "osmium>=3.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    package_data={
        "mrnet4gmns": ["*.csv"],
    },
    include_package_data=True,
    keywords="multi-resolution network GMNS transportation GIS OSM",
)

