# coding: utf-8
from __future__ import unicode_literals, absolute_import

import numpy as np

from .base import FilterTestCase
from universalimages.filters.xmp.v01 import Xmp_API

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

    def assertCrop(self, context, reference):
        crop = (
            context['left'], context['top'], context['right'], context['bottom']
        )
        self.assertEqual(crop, reference)

    def test_xmp_class(self):

        size = 1200, 900
        filt = self.get_filter('universalimages.filters.rmd', 'rmd()')
        self.load_file('monks-regions.jpg', filt.engine)
        api = Xmp_API(filt.engine.metadata)

        # Check the filter methods
        self.assertTrue(api.check_valid(size))
        self.assertTrue(api.check_allowed())

        # Check the meta data
        area = api.get_area_values_for('Xmp.rmd.CropArea')
        self.assertEqual(area['x'], 0.5181107954545454)
        self.assertEqual(area['y'], 0.5274621212121212)
        self.assertEqual(area['w'], 0.9026988636363636)
        self.assertEqual(area['h'], 0.8011363636363636)
        self.assertEqual(area['MinWidth'], 400)

        area = api.get_area_values_for(b'Xmp.rmd.SafeArea')
        self.assertEqual(area['x'], 0.4776278409090909)
        self.assertEqual(area['y'], 0.5821496212121212)
        self.assertEqual(area['w'], 0.5987215909090909)
        self.assertEqual(area['h'], 0.556344696969697)
        self.assertEqual(area['MaxWidth'], 320)

        areas = api.get_area_values_for_array('Xmp.rmd.RecommendedFrames')
        self.assertEqual(len(areas), 2)
        area = areas[0]
        self.assertEqual(area['x'], 0.4557883522727273)
        self.assertEqual(area['y'], 0.5243844696969697)
        self.assertEqual(area['w'], 0.7120028409090909)
        self.assertEqual(area['h'], 0.9512310606060606)
        self.assertEqual(area['MinAspectRatio'], 1)
        self.assertEqual(area['MaxAspectRatio'], 1)

        area = areas[1]
        self.assertEqual(area['x'], 0.4362571022727273)
        self.assertEqual(area['y'], 0.5712594696969697)
        self.assertEqual(area['w'], 0.71484375)
        self.assertEqual(area['h'], 0.6283143939393939)
        self.assertEqual(area['MinWidth'], 340)
        self.assertEqual(area['MaxWidth'], 360)

        area = api.get_area_values_for('Xmp.rmd.PivotPoint')
        self.assertEqual(area, {})

    def test_small_crop_exact_safe_area1(self):
        def config_context(context):
            context.request.width = 320

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('monks-regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (214, 274, 932, 774))
        fltr.context.transformer.img_operation_worker()
        self.assertCrop(fltr.context.request.crop, (214, 274, 932, 774))
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 320)
        # Target aspect = 3:2, but should be higher because of the safety area
        self.assertEqual(len(image), 223)

    def test_small_crop_less_than_safe_area1(self):
        def config_context(context):
            context.request.width = 240
            context.request.height = 160

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('monks-regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (181, 274, 932, 774))
        fltr.context.transformer.img_operation_worker()
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 240)
        self.assertEqual(len(image), 160)

    def test_small_crop_less_than_safe_area2(self):
        def config_context(context):
            context.request.width = 200
            context.request.height = 200

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('monks-regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (214, 116, 932, 834))
        fltr.context.transformer.img_operation_worker()
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 200)
        self.assertEqual(len(image), 200)

    def test_small_crop_less_than_safe_area3(self):
        def config_context(context):
            context.request.width = 300
            context.request.height = 150

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('monks-regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (117, 274, 1119, 774))
        fltr.context.transformer.img_operation_worker()
        image = np.array(fltr.engine.image)
        self.assertEqual(len(image[0]), 300)
        self.assertEqual(len(image), 150)

    def test_small_crop_less_than_safe_area4(self):
        def config_context(context):
            context.request.width = 200
            context.request.height = 300

        fltr = self.get_filter('universalimages.filters.rmd', 'rmd()',
                               config_context=config_context)
        self.assertFalse(fltr.context.request.should_crop)

        self.load_file('monks-regions.jpg', fltr.engine)
        fltr.run()
        self.assertTrue(fltr.context.request.should_crop)
        self.assertCrop(fltr.context.request.crop, (214, 114, 932, 835))
        fltr.context.transformer.img_operation_worker()
        image = np.array(fltr.engine.image)
        self.debug(image)
        self.assertEqual(len(image[0]), 200)
        self.assertEqual(len(image), 201)  # Image is cropped.