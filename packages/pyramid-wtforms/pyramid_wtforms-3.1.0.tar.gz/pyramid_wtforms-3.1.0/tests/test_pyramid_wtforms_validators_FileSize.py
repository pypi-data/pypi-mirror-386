import io
import unittest
from cgi import FieldStorage as CGIFieldStorage

from pyramid_wtforms.validators import FileSize, ValidationError
from pyramid_wtforms.storage import FieldStorage
from common import DummyForm, DummyField


class TestPyramidWTFormsValidatorsFileSize(unittest.TestCase):

    def setUp(self):
        self.form = DummyForm()
        self.field = DummyField()

    def test_should_init_normally(self):
        # mimic single file
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.txt'
        self.field.data.file = io.BytesIO(b'foo')
        self.assertIsNone(FileSize()(self.form, self.field))

        # multi files
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.txt'
        self.field.data[0].file = io.BytesIO(b'foo')
        self.field.data[1].filename = 'bar.txt'
        self.field.data[1].file = io.BytesIO(b'bar')
        self.assertIsNone(FileSize()(self.form, self.field))

    def test_file_size_is_higer_or_equal_than_lower_limit(self):
        # mimic single file
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.txt'
        test_file_data = b'foo'
        self.field.data.file = io.BytesIO(test_file_data)
        self.assertIsNone(
            FileSize(min=len(test_file_data)-1)(self.form, self.field))
        # boundary test
        self.assertIsNone(
            FileSize(min=len(test_file_data))(self.form, self.field))

        # multi files
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.txt'
        test_file_data1 = b'foo'
        self.field.data[0].file = io.BytesIO(test_file_data1)
        self.field.data[1].filename = 'bar.txt'
        test_file_data2 = b'bar123'
        self.field.data[1].file = io.BytesIO(test_file_data2)
        self.assertIsNone(
            FileSize(min=len(test_file_data1)-1)(self.form, self.field))
        # boundary test
        self.assertIsNone(
            FileSize(min=len(test_file_data1))(self.form, self.field))

    def test_raise_error_if_filesize_violate_limit(self):
        # mimic single file
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.txt'
        test_file_data = b'foo'
        self.field.data.file = io.BytesIO(test_file_data)
        with self.assertRaises(ValidationError):
            FileSize(min=len(test_file_data)+1)(self.form, self.field)

        # multi files
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.txt'
        test_file_data1 = b'foo'
        self.field.data[0].file = io.BytesIO(test_file_data1)
        self.field.data[1].filename = 'bar.txt'
        test_file_data2 = b'bar123'
        self.field.data[1].file = io.BytesIO(test_file_data2)
        with self.assertRaises(ValidationError):
            FileSize(min=len(test_file_data2)+1)(self.form, self.field)

    def test_should_pass_if_filesize_is_lower_or_equal_than_upper_limit(self):
        # mimic single file
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.txt'
        test_file_data = b'foo'
        self.field.data.file = io.BytesIO(test_file_data)
        self.assertIsNone(
            FileSize(max=len(test_file_data)+1)(self.form, self.field))
        # boundary test
        self.assertIsNone(
            FileSize(max=len(test_file_data))(self.form, self.field))

        # multi files
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.txt'
        test_file_data1 = b'foo'
        self.field.data[0].file = io.BytesIO(test_file_data1)
        self.field.data[1].filename = 'bar.txt'
        test_file_data2 = b'bar123'
        self.field.data[1].file = io.BytesIO(test_file_data2)
        self.assertIsNone(
            FileSize(max=len(test_file_data2)+1)(self.form, self.field))
        # boundary test
        self.assertIsNone(
            FileSize(max=len(test_file_data2))(self.form, self.field))

    def test_should_raise_error_if_filesize_violate_limit(self):
        # mimic single file
        self.field.data = FieldStorage(CGIFieldStorage())
        self.field.data.filename = 'foo.txt'
        test_file_data = b'foo'
        self.field.data.file = io.BytesIO(test_file_data)
        with self.assertRaises(ValidationError):
            FileSize(max=len(test_file_data)-1)(self.form, self.field)

        # multi files
        self.field.data = [FieldStorage(CGIFieldStorage()),
                           FieldStorage(CGIFieldStorage())]
        self.field.data[0].filename = 'foo.txt'
        test_file_data1 = b'foo'
        self.field.data[0].file = io.BytesIO(test_file_data1)
        self.field.data[1].filename = 'bar.txt'
        test_file_data2 = b'bar123'
        self.field.data[1].file = io.BytesIO(test_file_data2)
        with self.assertRaises(ValidationError):
            FileSize(max=len(test_file_data2)-1)(self.form, self.field)

    def test_should_count_file_size_automatically(self):
        min_size = 1
        max_size = 10

        base = 'b'
        file_size = FileSize(min=min_size, max=max_size, base=base)
        self.assertEqual(file_size.min_size, min_size)
        self.assertEqual(file_size.max_size, max_size)

        base = 'kb'
        file_size = FileSize(min=min_size, max=max_size, base=base)
        self.assertEqual(file_size.min_size, min_size * 1024)
        self.assertEqual(file_size.max_size, max_size * 1024)

        base = 'mb'
        file_size = FileSize(min=min_size, max=max_size, base=base)
        self.assertEqual(file_size.min_size, min_size * 1024**2)
        self.assertEqual(file_size.max_size, max_size * 1024**2)

        base = 'gb'
        file_size = FileSize(min=min_size, max=max_size, base=base)
        self.assertEqual(file_size.min_size, min_size * 1024**3)
        self.assertEqual(file_size.max_size, max_size * 1024**3)

    def test_should_pass_silently_if_the_field_is_not_present(self):
        self.field.data = None
        # the argument passed to FileSize here is not important
        self.assertIsNone(FileSize(min=1, max=10)(self.form, self.field))
