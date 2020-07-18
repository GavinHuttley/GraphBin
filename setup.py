#!/usr/bin/env python3

import os
from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

packages = ["graphbin"]
package_data = {
    "graphbin": [
        "graphbin/*.py",
        "graphbin/bidirectionalmap/*.py",
        "graphbin/labelpropagation/*.py",
    ]
}
data_files = [(".", ["LICENSE", "README.md"])]

setup(
    name='graphbin',
    version="1.1",
    author="Vijini Mallawaarachchi, Anuradha Wickramarachchi, and Yu Lin",
    author_email="vijini.mallawaarachchi@anu.edu.au",
    packages=packages,
    package_data=package_data,
    data_files=data_files,
    include_package_data=True,
    scripts=['bin/graphbin'],
    url='https://github.com/Vini2/graphbin',
    license='GPLv2',
    long_description_content_type="text/markdown",
    long_description=long_description,
    description='Refined binning of metagenomic contigs using assembly graphs.',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    install_requires=[
        "python-igraph",
        "setuptools"],
    zip_safe=False)
