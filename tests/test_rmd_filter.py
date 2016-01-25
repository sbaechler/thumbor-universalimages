from __future__ import unicode_literals, absolute_import
import unittest

from universalimages.filters.rmd import Filter
from os.path import abspath, join, dirname
from thumbor.context import Context
from thumbor.config import Config
from thumbor.loaders.file_loader import load


STORAGE_PATH = abspath(join(dirname(__file__), 'fixtures'))


class MyTestCase(unittest.TestCase):
    def setUp(self):
        config = Config(
            FILE_LOADER_ROOT_PATH=STORAGE_PATH
        )
        self.ctx = Context(config=config)

    def load_file(self, file_name):
        return load(self.ctx, file_name, lambda x: x).result()


    def test_something(self):
        self.assertEqual(True, False)
