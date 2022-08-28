def property_setter(name, default):
    def setter(obj, val):
        prop_type = type(default)
        private_name = "_" + name
        if isinstance(val, prop_type):
            setattr(obj, private_name, val)
        else:
            raise ValueError(f"{name} property of {obj} must be type {prop_type}")
    return setter


def property_getter(name, default):
    def getter(obj):
        private_name = "_" + name
        return getattr(obj, private_name, default)
    return getter


class ParameterizedMeta(type):

    def __new__(mcs, name, bases, namespace, **kwargs):
        return super().__new__(mcs, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kwargs):
        for param, default in kwargs.items():
            setattr(cls, param, property(property_getter(param, default), property_setter(param, default)))
        super().__init__(cls)


class Parameterized(metaclass=ParameterizedMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)
