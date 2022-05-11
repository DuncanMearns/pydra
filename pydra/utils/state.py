class state_descriptor:

    def __init__(self, val, instance=None):
        self.val = val
        self.instance = instance

    def __get__(self, instance, owner):
        return type(self)(self.val, instance)

    def __call__(self):
        setattr(self.instance, self.name, self.val)

    def __bool__(self):
        return getattr(self.instance, self.name) == self.val

    def __repr__(self):
        binding = "bound" if self.instance else "unbound"
        return f"<{binding} {self.name} object with value {self.val}>"

    @property
    def name(self):
        return type(self).__name__

    @classmethod
    def new_type(cls, name):
        return type(name, (cls,), {})
