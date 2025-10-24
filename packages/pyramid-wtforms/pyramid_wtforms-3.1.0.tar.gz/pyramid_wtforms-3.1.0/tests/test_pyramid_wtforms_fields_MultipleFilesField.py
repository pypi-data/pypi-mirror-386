import unittest
from cgi import FieldStorage as CGIFieldStorage

from pyramid import testing

from pyramid_wtforms import Form, MultipleFilesField
from pyramid_wtforms.storage import FieldStorage


class TestPyramidWTFormsFieldsMultipleFilesField(unittest.TestCase):

    def setUp(self):
        class TestForm(Form):
            files = MultipleFilesField('testfile')
        self.form = TestForm()

        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

    def tearDown(self):
        testing.tearDown()

    def test_process_data_with_valuelist_should_set_data_properly(self):
        test_objects = [FieldStorage(CGIFieldStorage())]
        self.form.files.process_formdata(test_objects)
        self.assertEqual(self.form.files.data, test_objects)

    def test_process_data_without_file_upload_should_set_data_to_None(self):
        self.form.files.process_formdata([b''])
        self.assertIsNone(self.form.files.data)

    def test_process_data_without_a_upload_files_should_raise_error(self):
        with self.assertRaises(ValueError):
            self.form.files.process_formdata([])
