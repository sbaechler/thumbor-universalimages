from __future__ import unicode_literals, absolute_import
import unittest

from thumbor.importer import Importer
from thumbor.transformer import Transformer

from universalimages.filters.rmd import Filter
from os.path import abspath, join, dirname
from thumbor.context import Context, RequestParameters
from thumbor.config import Config
from thumbor.engines.pil import Engine

STORAGE_PATH = abspath(join(dirname(__file__), 'fixtures'))

filter_data = {
    'async': False,
    'params': ({'regex': '[-]?(?:(?:[\\d]+\\.?[\\d]*)|(?:[\\d]*\\.?[\\d]+))',
                'parse': float},),
    'name': 'rmd',
    'defaults': None}


class RmdFilterTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from pyexiv2 import ImageMetadata
        except ImportError:
            raise ImportError('Pyexiv2 is not available. Please install it.')

    def setUp(self):
        config = Config(
            SECURITY_KEY='ACME-SEC',
            FILE_LOADER_ROOT_PATH=STORAGE_PATH,
            ENGINE = 'thumbor.engines.pil',
            STORAGE = 'thumbor.storages.no_storage'
        )
        # initialize the filter class.
        importer = Importer(config)
        importer.import_modules()
        self.ctx = Context(config=config, importer=importer)
        req = RequestParameters()
        self.ctx.request = req
        self.engine = Engine(self.ctx)
        self.ctx.modules.engine = self.engine
        req.engine = self.engine
        self.ctx.transformer = Transformer(self.ctx)

        Filter.compile_regex(filter_data)

    def load_file(self, file_name):
        with open(join(STORAGE_PATH, file_name), 'rb') as im:
            buffer = im.read()
        self.engine.load(buffer, None)

    def get_color_at(self, x, y):
        r, g, b = self.engine.image.getpixel((x, y))
        if r > b and r > g:
            return 'red'
        elif g > b and g > r:
            return 'green'
        elif b > r and b > g:
            return 'blue'
        elif r == 255 and b == 255 and g == 255:
            return 'white'
        return 'unknown color ({},{},{})'.format(r, g, b)

    def test_regions_image(self):
        self.load_file('regions.jpg')
        self.assertEqual(self.get_color_at(0, 0), 'blue')
        self.assertEqual(self.get_color_at(0, 100), 'green')
        self.assertEqual(self.get_color_at(320, 320), 'red')

        filter = Filter('1.0', self.ctx)

        # Check the filter methods
        self.assertTrue(filter._check_valid())
        self.assertTrue(filter._check_allowed())

        # Check the meta data
        area = filter.get_area_values_for('Xmp.rmd.CropArea')
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)
        self.assertEqual(area['w'], 1)
        self.assertEqual(area['h'], 0.75)
        self.assertEqual(area['MinWidth'], 480)

        area = filter.get_area_values_for(b'Xmp.rmd.SafeArea')
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)
        self.assertEqual(area['w'], 0.46875)
        self.assertEqual(area['h'], 0.3125)
        self.assertEqual(area['MaxWidth'], 300)

        areas = filter.get_area_values_for_array('Xmp.rmd.RecommendedFrames')
        self.assertEqual(len(areas), 1)
        area = areas[0]
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)
        self.assertEqual(area['w'], 1)
        self.assertEqual(area['h'], 1)
        self.assertEqual(area['MinAspectRatio'], 1)
        self.assertEqual(area['MaxAspectRatio'], 1)

        area = filter.get_area_values_for('Xmp.rmd.PivotPoint')
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)

