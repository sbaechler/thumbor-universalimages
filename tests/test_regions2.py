# coding: utf-8
from __future__ import unicode_literals, absolute_import

import numpy as np
from .base import FilterTestCase
from os.path import abspath, join, dirname

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
        image = self.get_filtered('regions2.jpg', 'universalimages.filters.rmd', 'rmd()')
        self.assertEqual(self.get_color_at(image, 0, 0), 'blue')
        self.assertEqual(self.get_color_at(image, 0, 100), 'green')
        self.assertEqual(self.get_color_at(image, 151, 201), 'red')

    def test_small_crop_exact_safe_area1(self):
        def config_context(context):
            context.request.width = 300
            context.request.height = 200

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (150, 200, 450, 400))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (150, 200, 450, 400))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 300)
        self.assertEqual(len(image), 200)
        # self.debug(image)
        self.assertEqual(self.get_color_at(image, 0, 0), 'red')

    def test_small_crop_less_than_safe_area1(self):
        def config_context(context):
            context.request.width = 240
            context.request.height = 160

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (150, 200, 450, 400))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (150, 200, 450, 400))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 240)
        self.assertEqual(len(image), 160)
        self.assertEqual(self.get_color_at(image, 0, 0), 'red')

    def test_small_crop_less_than_safe_area2(self):
        def config_context(context):
            context.request.width = 200
            context.request.height = 200

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (150, 133, 450, 433))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (150, 133, 450, 433))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 200)
        self.assertEqual(len(image), 200)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 0, 88), 'red')

    def test_small_crop_less_than_safe_area3(self):
        def config_context(context):
            context.request.width = 300
            context.request.height = 150

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        # 400x200
        self.assertCrop(fltr.context.request.crop, (83, 200, 483, 400))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (83, 200, 483, 400))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 300)
        self.assertEqual(len(image), 150)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 51, 0), 'red')

    def test_small_crop_less_than_safe_area4(self):
        def config_context(context):
            context.request.width = 200
            context.request.height = 300

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        # 300 x 450
        self.assertCrop(fltr.context.request.crop, (150, 89, 450, 539))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (150, 89, 450, 539))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 200)
        self.assertEqual(len(image), 300)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        self.assertEqual(self.get_color_at(image, 0, 78), 'red')  # (450/640) * (200-89)

    def test_linear_crop_1(self):
        def config_context(context):
            context.request.width = 400
            context.request.height = 300

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (37, 103, 570, 503))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (37, 103, 570, 503))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 400)
        self.assertEqual(len(image), 300)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        # (400/533) * (150 - 37), (400/533) * (200 - 103)
        self.assertEqual(self.get_color_at(image, 85, 73), 'red')

    def test_linear_crop_2(self):
        def config_context(context):
            context.request.width = 480
            context.request.height = 480

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (55, 80, 535, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (55, 80, 535, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 480)
        self.assertEqual(len(image), 480)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        # (480/480) * (150 - 55), (480/480) * (200 - 80)
        self.assertEqual(self.get_color_at(image, 95, 120), 'red')

    def test_linear_crop_3(self):
        # Target height is larger than Crop MinHeight, so the full crop area is used.
        def config_context(context):
            context.request.width = 400
            context.request.height = 400

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('regions2.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (55, 80, 535, 560))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (55, 80, 535, 560))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 400)
        self.assertEqual(len(image), 400)
        self.assertEqual(self.get_color_at(image, 0, 0), 'green')
        # (400/480) * (150 - 55), (400/480) * (200 - 80)
        self.assertEqual(self.get_color_at(image, 83, 100), 'red')