import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trading_bot",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A trading bot using Alpaca Trade API running on AWS EC2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Champ3624/trading_bot",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pandas",
        "yfinance",
        "numpy",
        "scipy",
        "requests"
    ],
)
