from setuptools import setup, find_packages

setup(
    name="nltkbleud",  # package name on PyPI
    version="0.1.0",
    author="pixelpilot24",
    author_email="pixelpilot24@gmail.com",
    description="package containing the BLEUD class.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.6",
)
