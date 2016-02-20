Universal Images Filter for Thumbor
===================================

This is a proof of concept prototype for the 
[Universalimages](https://www.w3.org/community/universalimages/) XMP standard.

Installation
------------

Install [Boost](http://www.boost.org/), 
[Boost.python](http://www.boost.org/libs/python/doc/index.html)
and exiv2:

    brew install boost boost-python    
    brew install exiv2 pyexiv2
    
This installs pyexiv2 in the homebrew python folder. If you already have a virtualenv, you 
have to recreate it.

For Ubuntu just install pyexiv2:

    apt-get install python-pyexiv2

The filter requires at least version 6 of Thumbor.
    
    pip install -r 'thumbor >= 6.0.0b3'
    pip install git+http://github.com/sbaechler/thumbor-universalimages.git

Add `universalimages.filters.rmd` to `thumbor.conf.FILTERS`.

Usage
-----

Refer to the [Thumbor](https://github.com/thumbor/thumbor/wiki) documentation.

To enable responsive metadata processing add the rmd filter like so: `/filters:rmd()/`.
