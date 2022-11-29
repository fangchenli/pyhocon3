#!/usr/bin/env python

from setuptools import setup


setup(
    name='pyhocon',
    version='0.3.59',
    description='HOCON parser for Python',
    long_description='pyhocon is a HOCON parser for Python. Additionally we provide a tool (pyhocon) to convert any HOCON '
                     'content into json, yaml and properties format.',
    keywords='hocon parser',
    license='Apache License 2.0',
    author='Francois Dang Ngoc',
    author_email='francois.dangngoc@gmail.com',
    url='http://github.com/chimpler/pyhocon/',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=[
        'pyhocon',
    ],
    install_requires=['pyparsing~=2.0'],
    extras_require={
        'Duration': ['python-dateutil>=2.8.0']
    },
    tests_require=['pytest', 'mock==3.0.5'],
    entry_points={
        'console_scripts': [
            'pyhocon=pyhocon.tool:main'
        ]
    },
    test_suite='tests',
)
