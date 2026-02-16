from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md") as f:
    long_description = f.read()

setup(
    name="libbtcr2",
    version="0.3.2",
    packages=find_packages(),
    install_requires=requirements,
    author="Will Abramson",
    author_email="will@legreq.com",
    description="Experimental python implementation of the did:btcr2 Method Specification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url='https://github.com/yourusername/mypackage',
)
