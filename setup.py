# coding: utf-8
from distutils.core import setup

setup(
        name='universalimages',
        version='0.1',
        packages=['universalimages', 'universalimages.filters', 'universalimages.filters.xmp'],
        url='https://github.com/sbaechler/thumbor-universalimages',
        license='MIT',
        keywords='rmd responsive',
        author='Simon Bächler',
        author_email='b@chler.com',
        description='A Thumbor Filter that interprets the Universal Images Metadata'
)
