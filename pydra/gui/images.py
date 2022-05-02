from PyQt5.QtGui import QPixmap
import pkg_resources


def get_image(image_name):
    return QPixmap(
        pkg_resources.resource_filename(__name__, "./icons/" + image_name)
    )


class IconDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, item):
        return get_image(super().__getitem__(item))


icons = IconDict({
    "python_logo": "python_logo.png",
})
