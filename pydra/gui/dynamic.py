import numpy as np
from ..utils.cache import TempCache


class GUICache(TempCache):

    def __init__(self, cachesize, arr_cachesize):
        super().__init__(cachesize, arr_cachesize)

    def update(self, new_data):
        for key, val in new_data.items():
            try:
                self.__getattribute__("new_" + key)(val)
            except AttributeError:
                setattr(self, key, val)

    def new_data(self, data: dict):
        # for k, vals in data.items():
        #     print(k, vals)
        return

    def new_array(self, arr: np.ndarray):
        return

    def new_events(self, events: list):
        for t, data in events:
            self.append_event(t, data)
        return


class DynamicUpdate:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cachesize = kwargs.get("cachesize")
        arr_cachesize = kwargs.get("arr_cachesize", cachesize)
        self.cache = GUICache(cachesize, arr_cachesize)

    def dynamicUpdate(self):
        return
