import unittest

from pyramid import testing

from pyramid_wtforms.forms import SecureForm


class MyTestForm(SecureForm):
    pass


class TestPyramidWTFormsFormsSecureForm(unittest.TestCase):

    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_foo(self):
        test_form = MyTestForm(meta={'csrf_context': self.request.session})
        self.assertEqual(
            test_form.csrf_token.current_token,
            self.request.session.get_csrf_token()
        )

        # mimic session invalidate
        new_session = 'new session'
        self.request.session['_csrft_'] = new_session
        test_form = MyTestForm(meta={'csrf_context': self.request.session})
        self.assertEqual(
            test_form.csrf_token.current_token,
            new_session
        )
        self.assertEqual(
            test_form.csrf_token.current_token,
            self.request.session.get_csrf_token()
        )
