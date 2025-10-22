from pathlib import Path

from setuptools import find_packages, setup

with Path("README.md").open(encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="personallize",
    version="1.0.0",
    packages=find_packages(),
    description="Biblioteca Python com ferramentas essenciais para desenvolvimento de RPA e ML, oferecendo recursos para conexão com bancos de dados, logging, ORM e monitoramento de performance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Miguel Tenório",
    author_email="deepydev42@gmail.com",
    url="https://github.com/MiguelTenorio42/personallize",
    project_urls={
        "Homepage": "https://github.com/MiguelTenorio42/personallize",
        "Bug Reports": "https://github.com/MiguelTenorio42/personallize/issues",
        "Source": "https://github.com/MiguelTenorio42/personallize",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: System :: Logging",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    keywords="rpa, ml, database, logging, orm, selenium, webdriver, performance",
    python_requires=">=3.13",
    install_requires=[
        "selenium>=4.0.0",
        "webdriver-manager>=3.8.0",
        "sqlalchemy>=2.0.0",
        "pymysql>=1.0.0",
        "psycopg2-binary>=2.9.0",
        "pyodbc>=4.0.0",
        "psutil>=5.8.0",
        "colorama>=0.4.4",
        "rich>=12.0.0",
        "tzdata>=2021.1",
    ],
    extras_require={
        "dev": [
            "ruff>=0.1.0",
            "mypy>=0.800",
        ],
    },
)
