from setuptools import setup, find_packages

setup(
    name="github-chatbot",
    version="1.0.4",
    packages=find_packages(),
    install_requires=[
        "click",
        "requests",
        "python-dotenv",
        "rich",
        "openai",
        "cryptography"
    ],
    entry_points={
        "console_scripts": [
            "gchat=cli.main:cli",
        ],
    },
)