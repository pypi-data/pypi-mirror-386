#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import fnmatch
from setuptools import setup, find_packages


# Path to the directory that contains this setup.py file.
base_dir = os.path.abspath(os.path.dirname(__file__))

def find_files(directory):
    matches = []

    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, '*'):
            matches.append(os.path.join(root, filename))

    return matches


setup(
    name="meeko",
    version='0.7.1',
    author="Forli Lab",
    author_email="forli@scripps.edu",
    url="https://github.com/forlilab/meeko",
    description='Python package for preparing small molecule for docking',
    long_description=open(os.path.join(base_dir, 'README.md')).read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license="LGPL-2.1",
    keywords=["molecular modeling", "drug design",
            "docking", "autodock"],
    classifiers=[
        'Environment :: Console',
        'Environment :: Other Environment',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: C++',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Software Development :: Libraries'
    ],
    entry_points={
        'console_scripts': [
            'mk_export.py=meeko.cli.mk_export:main',
            'mk_prepare_ligand.py=meeko.cli.mk_prepare_ligand:main',
            'mk_prepare_receptor.py=meeko.cli.mk_prepare_receptor:main'
        ]
    }
)
