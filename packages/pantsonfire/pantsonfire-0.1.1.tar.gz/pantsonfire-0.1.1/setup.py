from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name="pantsonfire",
    version="0.1.1",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pantsonfire=pantsonfire.cli:main",
        ],
    },
    author="Sean McDonald",
    author_email="",
    description="Find wrong information in technical docs online",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seanmcdonald/pantsonfire",
    project_urls={
        "Bug Reports": "https://github.com/seanmcdonald/pantsonfire/issues",
        "Source": "https://github.com/seanmcdonald/pantsonfire",
        "Documentation": "https://github.com/seanmcdonald/pantsonfire#readme",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "Topic :: Utilities",
    ],
    keywords="documentation, verification, fact-checking, technical-docs, ai, llm, web-scraping",
    python_requires=">=3.8",
)
