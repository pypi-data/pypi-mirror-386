from wtforms.widgets import *
from markupsafe import Markup


class MultipleFilesInput:
    """Render multiple files input chooser field."""

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('multiple', 'multiple')
        return Markup('<input %s>' % html_params(name=field.name, type='file', **kwargs))
