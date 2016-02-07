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

Currently the filter requires a custom branch of thumbor which supports xmp metadata.

`pip install -e git+git@github.com:sbaechler/thumbor-universalimages.git@56ce1f7a714571ba41827d7adab6d8f01595695c#egg=universalimages`.

`pip install git+https://github.com/sbaechler/thumbor-universalimages`.

Add `universalimages.filters.rmd` to `thumbor.conf.FILTERS`.

