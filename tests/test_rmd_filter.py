# coding: utf-8
from __future__ import unicode_literals, absolute_import
import unittest

import mock
import numpy as np

from .base import FilterTestCase
from thumbor.importer import Importer
from thumbor.transformer import Transformer

from universalimages.filters.rmd import Filter
from universalimages.filters.xmp.v01 import Xmp_API

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


class RmdFilterUnittestsTestCase(FilterTestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from pyexiv2 import ImageMetadata
        except ImportError:
            raise ImportError('Pyexiv2 is not available. Please install it.')

    def get_fixture_path(self, name):
        return join(STORAGE_PATH, name)

        
    # def get_context(self):
    #     config = Config(
    #         SECURITY_KEY='ACME-SEC',
    #         FILE_LOADER_ROOT_PATH=STORAGE_PATH,
    #         ENGINE = 'thumbor.engines.pil',
    #         STORAGE = 'thumbor.storages.no_storage'
    #     )
    #     # initialize the filter class.
    #     importer = Importer(config)
    #     importer.import_modules()
    #     ctx = Context(config=config, importer=importer)
    #     req = RequestParameters()
    #     ctx.request = req
    #     engine = Engine(ctx)
    #     ctx.request.engine = engine
    #     ctx.transformer = Transformer(ctx)
    #     return ctx, engine
    #
    #

    def load_file(self, file_name, engine):
        with open(join(STORAGE_PATH, file_name), 'rb') as im:
            buffer = im.read()
        engine.load(buffer, None)

    def get_color_at(self, image, x, y):
        px = image[y][x]
        r, g, b = px[0], px[1], px[2]
        if r > b and r > g:
            return 'red'
        elif g > b and g > r:
            return 'green'
        elif b > r and b > g:
            return 'blue'
        elif r == 255 and b == 255 and g == 255:
            return 'white'
        return 'unknown color ({},{},{})'.format(r, g, b)

    def assertCrop(self, context, reference):
        crop = (
            context['left'], context['top'], context['right'], context['bottom']
        )
        self.assertEqual(crop, reference)

    def test_regions_image(self):
        image = self.get_filtered('regions.jpg', 'universalimages.filters.rmd', 'rmd()')
        self.assertEqual(self.get_color_at(image, 0, 0), 'blue')
        self.assertEqual(self.get_color_at(image, 0, 100), 'green')
        self.assertEqual(self.get_color_at(image, 171, 221), 'red')

    def test_xmp_class(self):
        def config_context(context):
            context.request.width = 640
            context.request.height = 640

        size = 640, 640

        filt = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)

        self.load_file('regions.jpg', filt.engine)
        api = Xmp_API(filt.engine.metadata)

        # Check the filter methods
        self.assertTrue(api.check_valid(size))
        self.assertTrue(api.check_allowed())

        # Check the meta data
        area = api.get_area_values_for('Xmp.rmd.CropArea')
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)
        self.assertEqual(area['w'], 1)
        self.assertEqual(area['h'], 0.75)
        self.assertEqual(area['MinWidth'], 480)

        absolute_values = api.stArea_to_absolute(area, size)
        self.assertEqual(absolute_values, (0, 80, 640, 560))

        area = api.get_area_values_for(b'Xmp.rmd.SafeArea')
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)
        self.assertEqual(area['w'], 0.46875)
        self.assertEqual(area['h'], 0.3125)
        self.assertEqual(area['MaxWidth'], 300)

        absolute_values = api.stArea_to_absolute(area, size)
        self.assertEqual(absolute_values, (170, 220, 470, 420))

        areas = api.get_area_values_for_array('Xmp.rmd.RecommendedFrames')
        self.assertEqual(len(areas), 1)
        area = areas[0]
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)
        self.assertEqual(area['w'], 1)
        self.assertEqual(area['h'], 1)
        self.assertEqual(area['MinAspectRatio'], 1)
        self.assertEqual(area['MaxAspectRatio'], 1)

        absolute_values = api.stArea_to_absolute(area, size)
        self.assertEqual(absolute_values, (0, 0, 640, 640))

        area = api.get_area_values_for('Xmp.rmd.PivotPoint')
        self.assertEqual(area['x'], 0.5)
        self.assertEqual(area['y'], 0.5)

    def test_crop_only_original_size(self):
        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()')
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (0, 80, 640, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (0, 80, 640, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')

    def test_crop_only_width(self):
        def config_context(context):
            context.request.width = 480

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (0, 80, 640, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (0, 80, 640, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')

    def test_crop_only_height(self):
        def config_context(context):
            context.request.height = 480

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (0, 80, 640, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (0, 80, 640, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')

    # @unittest.skip
    # def test_crop_width_and_height(self):
    #     context, engine = self.get_context()
    #     context.request.height = 480
    #     context.request.width = 480
    #     self.load_file('regions.jpg', engine)
    #     filt = Filter('', context)
    #     filt.xmp.metadata = engine.metadata
    #     self.assertFalse(context.request.should_crop)
    #     filt.rmd()
    #     self.assertTrue(context.request.should_crop)
    #     self.assertCrop(context.request.crop, (0, 0, 640, 640))

    def test_small_crop_exact_safe_area(self):
        def config_context(context):
            context.request.width = 300
            context.request.height = 200

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (170, 220, 470, 420))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (170, 220, 470, 420))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'red')

    def test_small_crop_less_than_safe_area1(self):
        def config_context(context):
            context.request.width = 240
            context.request.height = 160

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (170, 220, 470, 420))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (170, 220, 470, 420))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'red')

    def test_small_crop_less_than_safe_area2(self):
        def config_context(context):
            context.request.width = 200
            context.request.height = 200

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (170, 170, 470, 470))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (170, 170, 470, 470))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 0, 50), 'red')

    def test_small_crop_less_than_safe_area3(self):
        def config_context(context):
            context.request.width = 300
            context.request.height = 150

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        # 400x200
        self.assertCrop(fltr.context.request.crop, (120, 220, 520, 420))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (120, 220, 520, 420))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 38, 5), 'red')  # 50 * 3/4

    def test_small_crop_less_than_safe_area4(self):
        def config_context(context):
            context.request.width = 200
            context.request.height = 300

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (170, 95, 470, 545))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (170, 95, 470, 545))
        image = np.array(fltr.engine.image)
        # 300 x 450
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 0, 125), 'red')  # 200 * 2/3

    def test_linear_crop_1(self):
        def config_context(context):
            context.request.width = 400
            context.request.height = 300

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (53, 120, 587, 520))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (53, 120, 587, 520))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 100, 75), 'red')

    def test_linear_crop_2(self):
        def config_context(context):
            context.request.width = 480
            context.request.height = 480

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (80, 80, 560, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (80, 80, 560, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 90, 140), 'red')  # 170 - 80, 220 - 80
        self.assertEqual(self.get_color_at(image, 120, 140), 'red')

    def test_linear_crop_3(self):
        def config_context(context):
            context.request.width = 400
            context.request.height = 400

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (80, 80, 560, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (80, 80, 560, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 75, 117), 'red')
