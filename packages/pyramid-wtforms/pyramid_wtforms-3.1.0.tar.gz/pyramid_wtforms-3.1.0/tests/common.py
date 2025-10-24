class DummyForm(list):
    pass


class DummyField:

    def __init__(self, *args, **kwargs):
        self.data = None
        self.message = None
        self.id = 'foo'
        self.name = 'bar'
        self.errors = []

    def gettext(self, msg):
        pass
