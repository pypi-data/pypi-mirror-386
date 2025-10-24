# -*- coding:utf-8 -*-

"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""
from libopensesame.py3compat import *
from libopensesame import misc
from libopensesame.oslogging import oslogger
from libopensesame.exceptions import InvalidValue
import tempfile
import os
import sys
import glob
import shutil
import psutil


class FilePoolStore:
    """The `pool` object provides dict-like access to the file pool. When
    checking whether a file is in the file pool, several folders are
    searched.
    For more details, see `pool.folders()`.

    A `pool` object is created
    automatically when the experiment starts.

    In addition to the functions
    listed below, the following semantics are
    supported:

    __Examples__
    
    Basic use:

    ~~~ .python
    # Get the full path to a file in the file pool
    print(f'The full path to img.png is {pool["img.png"]}')
    # Check if a file is in the file pool
    if 'img.png' in pool:
        print('img.png is in the file pool')
    # Delete a file from the file pool
    del pool['img.png']
    # Walk through all files in the file pool. This retrieves the full paths.
    for path in pool:
        print(path)
    # Check the number of files in the file pool
    print(f'There are {len(pool)} files in the file pool')
    ~~~
    
    Get an image from the file pool and use a `Canvas` to show it.

    ~~~ .python
    image_path = pool['img.png']
    my_canvas = Canvas()
    my_canvas.image(image_path)
    my_canvas.show()
    ~~~
    
    [TOC]
    """
    def __init__(self, experiment, folder=None):
        """Constructor.

        Parameters
        ----------
        experiment : experiment
            The experiment object.
        folder : str, unicode, NoneType, optional
            The folder to use for the file pool, or `None` to create a new
            temporary folder.
        """
        self.experiment = experiment
        if folder is None:
            process_id = os.getpid()
            folder_suffix = f".opensesame_pool_{process_id}"
            self.__folder__ = tempfile.mkdtemp(suffix=folder_suffix)
            oslogger.debug(f'creating new pool folder: {folder_suffix}')
        else:
            oslogger.debug('reusing existing pool folder')
            self.__folder__ = folder
        oslogger.debug(f'pool folder is {self.__folder__}')

    def clean_up(self):
        """Removes the pool folder."""
        try:
            shutil.rmtree(self.__folder__)
        except Exception:
            oslogger.error('Failed to remove %s' % self.__folder__)
            
    def clean_up_leftover_folders(self):
        """Removes all pool folders that do not belong to any currently 
        running process.
        """
        current_process_ids = {proc.pid for proc in psutil.process_iter()}
        pattern = os.path.join(tempfile.gettempdir(), "*opensesame_pool_*")
        for folder in glob.glob(pattern):
            try:
                folder_process_id = int(folder.split('_')[-1])
                if folder_process_id not in current_process_ids:
                    try:
                        shutil.rmtree(folder)
                    except Exception as e:
                        oslogger.warning(
                            f'failed to delete leftover folder: {folder} ({e})')
                    else:
                        oslogger.debug(f'deleted leftover folder: {folder}')
            except ValueError:
                oslogger.error(
                    f'unexpected folder name format, skipping {folder}')
                
    def __contains__(self, path):
        """Checks if a file is in the file pool.

        Returns
        -------
        bool
            A bool indicating if the file is in the pool.
        """
        if path == '':
            return False
        return os.path.exists(self[path])

    def __delitem__(self, path):
        """Deletes a file from the file pool.

        Parameters
        ----------
        path : str, unicode
            The name of the file.
        """
        os.remove(self[path])

    def __getitem__(self, path):
        """
        visible: False

        desc: |
            Returns the full path to a file.

        arguments:
            path:
                desc: A filename. This can be any type, but will be coerced
                      to `unicode` if it is not `unicode`.

        returns:
            desc: The full path to the file.
            type:unicode
        """
        path = safe_decode(path)
        if path.strip() == '':
            raise InvalidValue(f'Cannot get empty filename from file pool')
        for folder in self.folders(include_experiment_path=True):
            _path = os.path.normpath(os.path.join(folder, path))
            if os.path.exists(_path):
                return _path
        return os.path.normpath(path)

    def __iter__(self):
        """
        visible: False

        returns:
                type:	file_pool_store_iterator
        """
        return file_pool_store_iterator(self)

    def __len__(self):
        """
        visible: False

        returns:
                desc:	The number of files in the file pool.
                type:	int
        """
        return len(self.files())

    def count_included(self):
        """{nodoc}

        returns:
            desc: The number of files that are in the main pool folder, i.e.
                  the folder that is included with the experiment.
            type: int
        """
        return len(os.listdir(self.folder()))

    def add(self, path, new_name=None):
        """Copies a file to the file pool.

        Parameters
        ----------
        path : str, unicode
            The full path to the file on disk.
        new_name : str, NoneType, optional
            A new name for the file in the pool, or None to use the file's
            original name.

        Examples
        --------
        >>> pool.add('/home/username/Pictures/my_ing.png')
        """
        if new_name is None:
            new_name = os.path.basename(path)
        shutil.copyfile(path, os.path.join(self.folder(), new_name))

    def files(self):
        """Returns all files in the file pool.

        Returns
        -------
        list
            A list of full paths.

        Examples
        --------
        >>> for path in pool.files():
        >>>     print(path)
        >>> # Equivalent to:
        >>> for path in pool:
        >>>     print(path)
        """
        _files = []
        for _folder in self.folders():
            for _file in os.listdir(_folder):
                if os.path.isfile(os.path.join(_folder, _file)):
                    _files.append(_file)
        return sorted(_files)

    def fallback_folder(self):
        """The full path to the fallback pool folder, which is the
        `__pool__` subfolder of the current experiment folder, or
        `None` if this folder does not exist. The fallback pool
        folder is mostly useful in combination with a versioning
        system, such as git, because it allows you to save the
        experiment as a plain-text file, even when having files
        in the file pool.
        
        Examples
        --------
        >>> if pool.fallback_folder() is not None:
        >>>     print('There is a fallback pool folder!')
        
        Returns
        -------
        str
        """
        _folders = self.folders()
        if len(_folders) < 2:
            return None
        return _folders[-1]

    def folder(self):
        """Gives the full path to the (main) pool folder. This is typically a
        temporary folder that is deleted when the experiment is finished.

        Returns
        -------
        unicode
            The full path to the main pool folder.

        Examples
        --------
        >>> print(f'The pool folder is here: {pool.folder()}')
        """
        if not os.path.exists(self.__folder__):
            oslogger.warning('recreating missing file-pool folder')
            os.mkdir(self.__folder__)
        return self.__folder__

    def in_folder(self, path):
        """Checks whether path is in the pool folder. This is different from
        the `path in pool` syntax in that it only checks the main pool folder,
        and not the fallback pool folder and experiment folder.

        Parameters
        ----------
        path : str
            A file basename to check.

        Returns
        -------
        bool

        Examples
        --------
        >>> print(pool.in_folder('cue.png'))
        """
        return os.path.exists(os.path.join(self.folder(), path))

    def folders(self, include_fallback_folder=True,
                include_experiment_path=False):
        """Gives a list of all folders that are searched when retrieving the
        full path to a file. These are (in order):

        1. The file pool folder
        itself, as returned by `pool.folder()`.
        2. The folder of the current
        experiment (if it exists)
        3. The fallback pool folder, as returned by
        `pool.fallback_folder()` (if it exists)

        Parameters
        ----------
        include_fallback_folder : bool, optional
            Indicates whether the fallback pool folder should be included if it
            exists.
        include_experiment_path : bool, optional
            Indicates whether the experiment folder should be included if it
            exists.

        Returns
        -------
        list
            A list of all folders.

        Examples
        --------
        >>> print('The following folders are searched for files:')
        >>> for folder in pool.folders():
        >>>     print(folder)
        """
        _folders = [self.folder()]
        if self.experiment.experiment_path is None or \
                not os.path.exists(self.experiment.experiment_path):
            return _folders
        fallback_folder = os.path.join(self.experiment.experiment_path,
                                       '__pool__')
        if include_fallback_folder and os.path.exists(fallback_folder):
            _folders.append(fallback_folder)
        if include_experiment_path:
            _folders.append(self.experiment.experiment_path)
        return _folders

    def rename(self, old_path, new_path):
        """Renames a file in the pool folder.

        Parameters
        ----------
        old_path : str, unicode
            The old file name.
        new_path : str, unicode
            The new file name.

        Examples
        --------
        >>> pool.rename('my_old_img.png', 'my_new_img.png')
        """
        path = self[old_path]
        dirname, basename = os.path.split(path)
        os.rename(path, os.path.join(dirname, new_path))

    def size(self):
        """Gets the combined size in bytes of all files in the file pool.
        
        Examples
        --------
        >>> print(f'The size of the file pool is {pool.size()} bytes')
                
        Returns
        -------
        int
        """
        return sum([os.path.getsize(self[path]) for path in self])


class FilePoolStoreIterator:

    def __init__(self, pool):

        self.pool = pool
        self.files = pool.files()

    def __iter__(self):

        return self

    def __next__(self):

        # For Python 3
        return self.next()

    def next(self):

        if len(self.files) == 0:
            raise StopIteration
        return self.files.pop()



# Alias for backwards compatibility
file_pool_store = FilePoolStore
file_pool_store_iterator = FilePoolStoreIterator
