class LiveStateMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def toggle_live(self, state):
        pass


class RecordStateMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def toggle_record(self, state):
        pass
