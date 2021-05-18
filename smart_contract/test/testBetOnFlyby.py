import os.path
import unittest

from boa3.boa3 import Boa3
from boa3_test.tests.test_classes.testengine import TestEngine


class TestExample(unittest.TestCase):
    engine: TestEngine

    @classmethod
    def setUpClass(cls):
        folders = os.path.abspath(__file__).split(os.sep)
        cls.dirname = '/'.join(folders[:-2])

        test_engine_installation_folder = cls.dirname   # Change this to your test engine installation folder
        cls.engine = TestEngine(test_engine_installation_folder)

    def test_example(self):
        path = f'{self.dirname}/src/BetOnFlyby.py'
        nef_path = path.replace('.py', '.nef')

        Boa3.compile_and_save(path, output_path=nef_path)

        self.engine.reset_engine()
        result = self.engine.run(nef_path, 'request_image_change')
        self.assertIsNone(result)  # calling_script_hash in the test engine is None
