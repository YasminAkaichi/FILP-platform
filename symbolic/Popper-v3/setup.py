# -*- coding: utf-8 -*-

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    # Distinct distribution name from symbolic/popper-core's setup.py
    # (also named "popper-ilp") — pip treats "popper-ilp" as a single
    # package and refuses to install two different versions of it side
    # by side, even though the importable Python package was already
    # renamed (popper -> popper_mdl) to avoid a runtime collision.
    name="popper-ilp-mdl",
    version="2.0.0",                        # Update this for every new version
    author="Andrew Cropper",
    author_email="andrew.cropper@cs.ox.ac.uk",
    description="Popper",
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=['run_popper_mdl'],
    install_requires=[
        'clingo',
        'pyswip'
    ],
    url="https://github.com/logic-and-learning-lab/Popper",
    scripts=['bin/popper-ilp'],
    packages=setuptools.find_packages()
    # classifiers=(                                 # Classifiers help people find your
        # "Programming Language :: Python :: 3"    # projects. See all possible classifiers
    # ),
)
