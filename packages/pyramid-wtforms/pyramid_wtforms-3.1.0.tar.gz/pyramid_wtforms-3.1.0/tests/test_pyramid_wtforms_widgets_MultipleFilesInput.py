import unittest

from pyramid_wtforms.widgets import MultipleFilesInput
from common import DummyField


class TestPyramidWTFormsWidgetsMultipleFilesInput(unittest.TestCase):

    def setUp(self):
        self.field = DummyField()

    def test_should_return_multiple_files_input_label(self):
        self.assertEqual(
            MultipleFilesInput()(self.field),
            '<input id="foo" multiple="multiple" name="bar" type="file">'
        )
