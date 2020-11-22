#!/usr/bin/python3

try:
    from rjgtoys.projects import setup
except ImportError:
    from setuptools import setup

setup(
    name = "rjgtoys-cli",
    version = "0.0.1",
    author = "Robert J. Gautier",
    author_email = "bob.gautier@gmail.com",
    url = "https://github.com/bobgautier/rjgtoys-CLI",
    description = ("Command-line tool components"),
    namespace_packages=['rjgtoys'],
    packages = ['rjgtoys','rjgtoys.cli'],
    install_requires = [
    ],
    extras_require = {
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
