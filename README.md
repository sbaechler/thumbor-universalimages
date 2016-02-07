Universal Images Filter for Thumbor
===================================

This is a proof of concept prototype and not production ready.

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

Currently the filter requires a custom branch of thumbor which supports xmp metadata.

    pip install git+http://github.com/sbaechler/thumbor.git@831501939ebd3be538c63fb617a3cdb8d995fa80
    git+http://github.com/sbaechler/thumbor-universalimages.git@294dad08b8c6cffec9aed6752cef5af7c2cdb1cd

Add `universalimages.filters.rmd` to `thumbor.conf.FILTERS`.

