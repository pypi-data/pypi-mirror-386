from setuptools import setup, find_packages

setup(
    name="eldartools",
    version="0.2.0",
    author="Eldar Eliyev",
    author_email="eldar@example.com",
    description="All-in-one Python utilities: strings, lists, dicts, numbers, files, dates, security.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
)
