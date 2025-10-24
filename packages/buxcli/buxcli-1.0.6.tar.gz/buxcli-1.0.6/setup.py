from setuptools import setup, find_packages

setup(
    name="buxcli",
    version="1.0.6",  
    packages=find_packages(),
    install_requires=[
        "inquirer",
        "rich",
        "click",
        "dotenv",
        "setuptools"
    ],
    entry_points={
        "console_scripts": [
            "buxcli=buxcli.main:cli",
        ],
    },
    author="Mohd. Rushaad Buxy",
    author_email="m.rushaadq@gmail.com",
    description="A simple CLI tool for alert you about your CLI.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rushaad2911/buxcli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
)
