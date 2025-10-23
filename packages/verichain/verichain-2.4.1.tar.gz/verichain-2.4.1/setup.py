#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Read README
this_directory = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(os.path.dirname(this_directory), 'README.md')
try:
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'VeriChain - Legal-grade accountability system for AI decisions'

setup(
    name="verichain",
    version="2.4.1",
    author="Fabio Petti",
    author_email="contact@verichain.com",
    description="Legal-grade accountability system for AI decisions with ATHENA, HELIOS, and ARES",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/verichain/verichain",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "cryptography>=41.0.0",
        "pynacl>=1.5.0",
        "canonicaljson>=2.0.0",
        "python-dateutil>=2.8.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "verichain=verichain.cli:main",
        ],
    },
)
