from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="openatlas",
    version="1.0.0",
    author="Harish Santhanalakshmi Ganesan",
    author_email="",
    description="An autonomous browser agent with web search and interactive browsing capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openatlas/openatlas",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'openatlas=openatlas.cli:main',
        ],
    },
    keywords="ai agent browser automation web-scraping llm claude gpt gemini",
    project_urls={
        "Bug Reports": "https://github.com/openatlas/openatlas/issues",
        "Source": "https://github.com/openatlas/openatlas",
    },
)
