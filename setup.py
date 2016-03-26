# coding: utf-8
from __future__ import unicode_literals
from setuptools import setup, find_packages

setup(
    name='universalimages',
    version='0.1.0',
    packages=find_packages(exclude=['docs', 'tests']),
    url='https://github.com/sbaechler/thumbor-universalimages',
    license='MIT',
    keywords='rmd responsive',
    author='Simon Bächler',
    author_email='b@chler.com',
    install_requires=['thumbor'],
    description='A Thumbor Filter that interprets the Universal Images Metadata',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
    ],
)
