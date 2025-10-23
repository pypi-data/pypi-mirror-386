from setuptools import setup, find_packages

setup(
    name="buxcli",  # Package name
    version="1.0",  # Version
    packages=find_packages(),  # Finds all packages automatically
    install_requires=[  # Dependencies
        "inquirer",
        "rich"
    ],
    entry_points={  # CLI command
        "console_scripts": [
            "buxcli=buxcli.main:cli",
        ],
    },
    author="Mohd. Rushaad Buxy",
    author_email="m.rushaadq@gmail.com",
    description="A simple CLI tool for project setup automation.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rushaad2911/Mycli",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
)
