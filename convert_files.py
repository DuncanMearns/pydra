import sys
# import tkinter, tkFileDialog
from tkinter import Tk, filedialog
import os
import numpy as np
import pandas as pd


def pickdir(path='.'):
    root = Tk()
    root.withdraw()
    dirname = filedialog.askdirectory(parent=root,initialdir=".",title='Please select a directory')

    root.destroy()
    if len(dirname ) > 0:
        return dirname
    else:
        print("No directory picked, exiting!")
        sys.exit()


def get_files(directory, return_paths=True):
    """Lists the files in a directory sorted alphabetically

    N.B. For getting folders in a directory use getDirectories

    Parameters
    ----------
    directory : str
        Path to a directory containing files
    return_paths : bool, default False
        Return paths as well as file names

    Returns
    -------
    file_names [, file_paths] : list [, list]
        Files in a directory (list of strings), if return_paths==True returns complete paths as second argument
    """
    filenames = os.listdir(directory)
    remove_files = ['.DS_Store', 'Thumbs.db']
    for filename in remove_files:
        if filename in filenames:
            filenames.remove(filename)
    filenames = [filename for filename in filenames if os.path.isfile(os.path.join(directory, filename))]
    filenames.sort()
    if return_paths:
        filepaths = [os.path.join(directory, name) for name in filenames]
        return filenames, filepaths
    else:
        return filenames


if __name__ == "__main__":

    path = pickdir()
    fs = get_files(path, return_paths=False)

    avis = [os.path.splitext(f)[0] for f in fs if f.endswith('avi')]
    for avi in avis:
        try:
            metadata = np.load(os.path.join(path, avi + '.npy'))
            points = np.load(os.path.join(path, avi + '_points.npy'))
            tail_vector = points[:, -1] - points[:, 0]
            tail_angle = np.arctan2(tail_vector[:, 1], tail_vector[:, 0])
            timestamp = metadata[:, 1] - metadata[0, 1]
            cols = ['time', 'tail_angle', 'laser_on']
            try:
                df = pd.DataFrame(dict(zip(cols, [timestamp, tail_angle, metadata[:, 2]])), columns=cols)
            except ValueError:
                df = pd.DataFrame(dict(zip(cols, [timestamp, tail_angle[-len(timestamp):], metadata[:, 2]])), columns=cols)
            df.to_csv(os.path.join(path, avi + '.csv'), index=False)
        except IOError:
            print('No metadata file for {}'.format(avi))
