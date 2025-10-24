import warnings

from wtforms.form import Form
from wtforms.csrf.core import CSRF as _CSRF


class CSRF(_CSRF):
    """This class uses pyramid builtin csrf facility."""

    def setup_form(self, form):
        self.csrf_context = form.meta.csrf_context
        return super(CSRF, self).setup_form(form)

    def generate_csrf_token(self, csrf_token):
        return self.csrf_context.get_csrf_token()


class SecureForm(Form):
    """The form which enables csrf protection default"""

    def __init__(self, *args, **kwargs):
        warnings.warn('For better test support, use Pyramid builtin csrf checking facility instead. '
                      'See https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/security.html#auto-csrf-checking for more information. '
                      'SecureForm will be removed in version 4.0.0.',
                      DeprecationWarning)
        super().__init__(*args, **kwargs)

    class Meta:
        csrf = True
        csrf_class = CSRF
