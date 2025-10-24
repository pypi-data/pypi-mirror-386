import unittest
from cgi import FieldStorage as CGIFieldStorage

from pyramid_wtforms.validators import FileQuantity
from pyramid_wtforms.storage import FieldStorage
from common import DummyForm, DummyField


class TestPyramidWTFormsValidatorsFileQuantity(unittest.TestCase):

    def setUp(self):
        self.form = DummyForm()
        self.field = DummyField()

    def test_should_not_work_against_single_file_upload(self):
        self.field.data = FieldStorage(CGIFieldStorage())
        with self.assertRaises(ValueError):
            FileQuantity(min=1, max=1)(self.form, self.field)

    def test_should_work_against_multi_files_upload(self):
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.assertIsNone(FileQuantity(min=1, max=3)(self.form, self.field))

        # boundary tests
        self.assertIsNone(FileQuantity(min=2, max=3)(self.form, self.field))
        self.assertIsNone(FileQuantity(min=1, max=2)(self.form, self.field))
        self.assertIsNone(FileQuantity(min=2, max=2)(self.form, self.field))

    #def test_should_pass_silently_if_the_field_is_not_present(self):
    #    self.field.data = None
    #    # the argument passed to FileQuantity here is not important
    #    self.assertIsNone(FileQuantity(min=1, max=2)(self.form, self.field))
