import sys
from setuptools import setup, find_packages, Command
from distutils import log

setup(
    name='gfregression',
    version='3.2.0',
    author="Google Fonts Project Authors",
    description="GFRegression lib",
    url="https://github.com/googlefonts/gfregression",
    license="Apache Software License 2.0",
    package_dir={"": "Lib"},
    packages=["gfregression"],
    package_data={"gfregression": [
        "gf_families_ignore_camelcase.json",
        "udhr_all.txt",
    ]},
    entry_points={
        "console_scripts": [
            "find-camelcase-families = gfregression.gf_families_ignore_camelcase:main",
        ],
    },
    install_requires=[
        "fontdiffenator",
        "flask",
        "requests",
        "rethinkdb==2.3.0.post6",
    ],
)
