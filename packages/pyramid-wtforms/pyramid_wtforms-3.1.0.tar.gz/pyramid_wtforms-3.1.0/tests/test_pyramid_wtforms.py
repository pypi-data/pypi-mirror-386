import unittest


class TestPyramidWTForms(unittest.TestCase):

    def test_pyramid_wtforms_should_have_essential_elements(self):
        import wtforms
        import pyramid_wtforms

        ori_elements = set()
        for i in dir(wtforms):
            if i[0].isupper():
                ori_elements.add(i)
        
        pw_elements = set()
        for i in dir(pyramid_wtforms):
            if i[0].isupper():
                pw_elements.add(i)

        pw_extra_elements = set(['MultipleCheckboxField', 'MultipleFilesField', 'SecureForm'])

        self.assertEqual( ori_elements | pw_extra_elements, pw_elements)
