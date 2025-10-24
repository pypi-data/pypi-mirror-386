from setuptools import setup, find_packages

setup(
    name="passgenpro",
    version="0.1.0",
    author="Eldar Eliyev",
    author_email="eldar@example.com",
    description="Simple yet powerful password generator library.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.7",
)
