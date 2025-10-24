import unittest

from pyramid_wtforms import Form, MultipleCheckboxField


class TestPyramidWTFormsFieldsMultipleCheckboxField(unittest.TestCase):

    def setUp(self):
        class TestForm(Form):
            cbs = MultipleCheckboxField('multicheckboxes')
        self.form = TestForm()

    def test_process_data_with_valuelist_should_set_data_properly(self):
        test_data = ['foo', 'bar']
        self.form.cbs.process_formdata(test_data)
        self.assertEqual(self.form.cbs.data, test_data)

        # empty string will transform to empty list
        self.form.cbs.process_formdata('')
        self.assertEqual([], self.form.cbs.data)

        # empty list will be the same
        self.form.cbs.process_formdata([])
        self.assertEqual([], self.form.cbs.data)

