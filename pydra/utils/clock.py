import time


class ClockMeta(type):
    """Metaclass for clock used to synchronize timestamps across GUI components."""

    def __init__(cls, name, bases, dct):
        cls._t0 = time.time()

    @property
    def t0(cls):
        return cls._t0

    @property
    def t(cls):
        return time.time() - cls._t0

    def reset(cls):
        cls._t0 = time.time()


class clock(metaclass=ClockMeta):
    pass
