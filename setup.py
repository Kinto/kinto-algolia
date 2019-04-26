#!/usr/bin/env python
from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.rst') as history_file:
    history = history_file.read()

REQUIREMENTS = [
    'algoliasearch',
    'kinto'
]

TEST_REQUIREMENTS = [
    'webtest',
]

ENTRY_POINTS = {
    'console_scripts': [
        'kinto-algolia-reindex = kinto_algolia.command_reindex:main'
    ],
}

setup(
    name='kinto-algolia',
    version='1.1.0',
    description="Index and search records using Algolia.",
    long_description=readme + '\n\n' + history,
    author='Rémy Hubscher',
    author_email='hubscher.remy@gmail.com',
    url='https://github.com/Kinto/kinto-algolia',
    packages=[
        'kinto_algolia',
    ],
    package_dir={'kinto_algolia': 'kinto_algolia'},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    license="Apache License (2.0)",
    zip_safe=False,
    keywords='kinto algolia index',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=TEST_REQUIREMENTS,
    entry_points=ENTRY_POINTS
)
