import unittest
from cgi import FieldStorage as CGIFieldStorage

from pyramid_wtforms.validators import FileRequired, StopValidation
from pyramid_wtforms.storage import FieldStorage
from common import DummyForm, DummyField


class TestPyramidWTFormsValidatorsFileRequired(unittest.TestCase):

    def setUp(self):
        self.form = DummyForm()

    def test_call_with_form_n_field_raise_error_if_data_is_invalid(self):
        dummy_field = DummyField()
        # mimic single invalid object
        dummy_field.data = 'invalid'
        with self.assertRaises(StopValidation):
            FileRequired()(self.form, dummy_field)

        # mimic multi invalid objects
        dummy_field.data = ['invalid', 'data']
        with self.assertRaises(StopValidation):
            FileRequired()(self.form, dummy_field)

        # the field is not present
        dummy_field.data = None
        with self.assertRaises(StopValidation):
            FileRequired()(self.form, dummy_field)

    def test_call_with_form_and_field_should_happen_nothing(self):
        dummy_field = DummyField()
        # mimic single file upload
        dummy_field.data = FieldStorage(CGIFieldStorage())
        self.assertIsNone(FileRequired()(self.form, dummy_field))

        # mimic multi files upload
        dummy_field.data = [FieldStorage(CGIFieldStorage()),
                            FieldStorage(CGIFieldStorage())]
        self.assertIsNone(FileRequired()(self.form, dummy_field))
