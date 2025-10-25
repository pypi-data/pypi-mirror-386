from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="apgard",
    version="0.1.8",
    author="Ariel Colon",
    author_email="ariel@apgardai.com",
    description="SDK for safeguarding AI chatbots and minors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ariel-colon/apgard.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "nest_asyncio>=1.6.0",
        "httpx>=0.28.1"
    ],
)