from setuptools import setup, find_packages

setup(
    name="eldar_finance_matrix",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    author="Eldar Eliyev",
    description="Financial calculations utility library",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/eldar/financetools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ]
)
