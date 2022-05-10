class conditional:
    """Decorator for conditional methods. Method is only called when condition returns True."""

    def __init__(self, method=None, condition=None):
        self.method = method
        self.condition = condition if condition else lambda obj: False
        self.object = None

    def __get__(self, instance, owner):
        self.object = instance
        return self.__call__

    def __call__(self, *args, **kwargs):
        if self.condition(self.object):
            self.method(self.object, *args, **kwargs)

    def when(self, condition):
        return type(self)(self.method, condition)
