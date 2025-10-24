import unittest
from cgi import FieldStorage as CGIFieldStorage

from pyramid_wtforms.validators import FileAllowed, ValidationError
from pyramid_wtforms.storage import FieldStorage
from common import DummyForm, DummyField


class TestPyramidWTFormsValidatorsFileAllowed(unittest.TestCase):

    def setUp(self):
        self.form = DummyForm()
        self.field = DummyField()

    def test_call_with_form_n_field_raise_error_if_ext_isnt_allowed(self):
        # mimic single file with txt ext, which is not allowed
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.txt'
        with self.assertRaises(ValidationError):
            FileAllowed(['jpg'])(self.form, self.field)

        # mimic multi files which ext name are not allowed
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.txt'
        self.field.data[1].filename = 'bar.jpg'
        with self.assertRaises(ValidationError):
            FileAllowed(['jpg'])(self.form, self.field)

    def test_call_with_form_n_field_should_pass_if_ext_are_allowed(self):
        # mimic single file with txt ext which is allowed
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.jpg'
        self.assertIsNone(FileAllowed(['jpg'])(self.form, self.field))

        # mimic multi files which ext name are all allowed
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.png'
        self.field.data[1].filename = 'bar.jpg'
        self.assertIsNone(FileAllowed(['jpg', 'png'])(self.form, self.field))

    def test_should_check_file_ext_in_case_insensitive(self):
        # single file checking
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.JPG'
        self.assertIsNone(FileAllowed(['jpg'])(self.form, self.field))

        # multi files checking
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.JPG'
        self.field.data[1].filename = 'bar.Png'
        self.assertIsNone(FileAllowed(['png', 'jpg'])(self.form, self.field))

    def test_should_pass_silently_if_the_field_is_not_present(self):
        self.field.data = None
        # the argument passed to FileAllowed here is not important
        self.assertIsNone(FileAllowed(['png'])(self.form, self.field))
