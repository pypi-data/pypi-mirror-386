"""
Week Service - PyPI Package Setup
Futbol maçlarını haftalara bölen ve puan durumu hesaplayan servis
"""
from setuptools import setup, find_packages

with open("README_PYPI.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="week-service",
    version="1.0.2",
    author="Monscer",
    author_email="your.email@example.com",
    description="Futbol maçlarını haftalara bölen ve puan durumu hesaplayan profesyonel servis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/week-service",
    packages=find_packages(),
    py_modules=['week_service', 'cli'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "psycopg[binary]>=3.1.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        'console_scripts': [
            'week-service=week_service.cli:main',
        ],
    },
)
