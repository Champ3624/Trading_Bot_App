from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="trading-bot",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A trading bot for calendar spread strategy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-bot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "trading-bot=trading_bot.run:main",
        ],
    },
    include_package_data=True,
    package_data={
        "trading_bot": ["templates/*"],
    },
) 