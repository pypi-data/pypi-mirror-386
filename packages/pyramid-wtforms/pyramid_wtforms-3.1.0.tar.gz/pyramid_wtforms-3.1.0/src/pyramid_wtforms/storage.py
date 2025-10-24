from cgi import FieldStorage as _CGIFieldStorage


class FieldStorage:
    """Replace cgi.FieldStorage with our own FieldStorage.

    cgi.FieldStorage does not support __bool__, so we need a simple wrapper
    to support this protocol for convenience."""

    def __init__(self, field_storage):
        self.field_storage = field_storage

    def __bool__(self):
        if isinstance(self.field_storage, _CGIFieldStorage):
            return True
        else:
            return False

    @property
    def file(self):
        return self.field_storage.file

    @file.setter
    def file(self, value):
        self.field_storage.file = value

    @property
    def filename(self):
        return self.field_storage.filename

    @filename.setter
    def filename(self, value):
        self.field_storage.filename = value
