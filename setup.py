import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trading_bot",
    version="0.1.0",
    author="Chuckie Sultan",
    author_email="championman5@gmail.com",
    description="A trading bot using Alpaca Trade API running on AWS EC2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Champ3624/Trading_Bot_App",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "numpy==1.21.6",
        "pandas==2.0.1",
        "pytz==2025.1",
        "requests==2.32.3",
        "scipy==1.15.2",
        "setuptools==75.8.0",
        "yfinance==0.2.55",
    ],
)
