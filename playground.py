from matplotlib import pyplot


def find_qt():
    import os, sys

    qtcore_dll = '\\Qt5Core.dll'

    dll_dir = os.path.dirname(sys.executable)
    if not os.path.isfile(dll_dir + qtcore_dll):
        path = os.environ['PATH']

        dll_dir = os.path.dirname(__file__) + '\\Qt5\\bin'
        if os.path.isfile(dll_dir + qtcore_dll):
            path = dll_dir + ';' + path
            os.environ['PATH'] = path
        else:
            for dll_dir in path.split(';'):
                if os.path.isfile(dll_dir + qtcore_dll):
                    break
            else:
                return

    try:
        os.add_dll_directory(dll_dir)
    except AttributeError:
        pass


find_qt()
