import unittest
from cgi import FieldStorage as CGIFieldStorage

from pyramid_wtforms.storage import FieldStorage


class TestPyramidWTFormsStorageFieldStorage(unittest.TestCase):

    def test_should_provide_simple_wrapper(self):
        cgi_field_storage = CGIFieldStorage()
        cgi_field_storage.file = 'foo'
        cgi_field_storage.filename = 'bar'

        field_storage = FieldStorage(cgi_field_storage)
        self.assertEqual(cgi_field_storage.file, field_storage.file)
        self.assertEqual(cgi_field_storage.filename, field_storage.filename)

    def test_should_support_bool_protocol(self):
        cgi_field_storage = CGIFieldStorage()
        field_storage = FieldStorage(cgi_field_storage)
        self.assertTrue(field_storage)

        field_storage = FieldStorage(None)
        self.assertFalse(field_storage)
