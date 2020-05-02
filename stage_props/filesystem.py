#!/usr/bin/env python3
import os
import pickle
import hashlib

from typing import List

FILESYSTEM_TEMPLATE = os.path.join(os.path.dirname(__file__), '..', 'resources', 'fs_template.pkl')


def win_path_join(dirname: str, basename: str) -> str:
    """Join path Windows style"""
    d = dirname.rstrip("\\")
    return f'{d}\\{basename}'


def win_path_dirname(path: str) -> str:
    """Retrieve only the directory part of a Windows file path"""
    dirname = '\\'.join(path.rstrip('\\').split('\\')[:-1])
    return 'c:\\' if dirname == 'c:' else dirname


def win_path_basename(path: str) -> str:
    """Retrieve only the basename(filename) part of a Windows file path"""
    return path.rstrip('\\').split('\\')[-1]


class VirtualFile:
    def __init__(self, name, physical_path, default_data=b'', default_size: int=0):
        self.name = name
        self.data = default_data
        self.physical_path = physical_path
        self.pos = 0
        self.default_size = default_size

    def read(self, n=-1):
        """Read n bytes from file"""
        if n == -1:
            n = len(self.data) - self.pos
        data = self.data[self.pos:min(self.pos + n, len(self.data))]
        self.pos += n
        return data

    def write(self, data):
        """Write data to file"""
        self.data = data

    def append(self, data):
        """Append data to the end of the file"""
        self.data += data

    def seek(self, pos):
        """Set the file's pointer position"""
        self.pos = min(pos, len(self.data))

    @property
    def size(self):
        """Get the current size of the file"""
        return max(len(self.data) if self.data else 0, self.default_size)

    def close(self):
        """Close file object. Automatically flush any written data to disk"""
        self.flush()

    def flush(self):
        """Flush any written data to disk"""
        dir_ = os.path.dirname(self.physical_path)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)
        with open(self.physical_path, 'wb') as fh:
            fh.write(self.data)

    @property
    def sha256(self):
        """Calculate SHA256 of file's data"""
        return hashlib.sha256(self.data).hexdigest()


class VirtualDirectory:
    def __init__(self, name, physical_path, parent_directory=None):
        self.name = name.rstrip('\\')
        self.physical_path = physical_path
        self.parent_directory = parent_directory
        self.child_directories = list()
        self.child_files = list()

    @property
    def full_path(self) -> str:
        if not self.parent_directory:
            return self.name
        return win_path_join(self.parent_directory.full_path, self.name)

    def create_directory(self, name: str) -> 'VirtualDirectory':
        """Create new child directory"""
        if not self.is_dir(name):
            self._create_directory(name)
        return next(dir_ for dir_ in self.child_directories if dir_.name.lower() == name.lower())

    def _create_directory(self, name: str):
        safe_name = os.path.basename(name)  # prevent directory traversal
        if not safe_name:
            raise Exception('Suspicious directory name! possible directory traversal attempt!')
        virtual_directory = VirtualDirectory(safe_name,
                                             physical_path=os.path.join(self.physical_path, safe_name),
                                             parent_directory=self)
        self.child_directories.append(virtual_directory)

    def create_file(self, name, default_size: int=0) -> VirtualFile:
        """Create new file under this directory"""
        if not self.is_file(name):
            self._create_file(name, default_size)
        return next(file_ for file_ in self.child_files if file_.name.lower() == name.lower())

    def _create_file(self, name: str, default_size: int=0):
        safe_name = os.path.basename(name)  # prevent directory traversal
        if not safe_name:
            raise Exception('Suspicious file name! possible directory traversal attempt!')
        virtual_file = VirtualFile(safe_name,
                                   physical_path=os.path.join(self.physical_path, safe_name + '.sample'),
                                   default_size=default_size)
        self.child_files.append(virtual_file)

    def exists(self, name):
        """Check if file or directory are childs of current directory"""
        return self.is_file(name) or self.is_dir(name)

    def is_file(self, name):
        """Check if file is a child of current directory"""
        return name.lower() in [file_.name.lower() for file_ in self.child_files]

    def is_dir(self, name):
        """Check if directory is a child of current directory"""
        return name.lower() in [dir_.name.lower() for dir_ in self.child_directories]

    def open_file(self, name):
        """Open existing file under current directory"""
        if not self.is_file(name):
            raise FileNotFoundError(name)
        return next(file_ for file_ in self.child_files if file_.name.lower() == name.lower())

    def open_dir(self, name):
        """Open existing sub-directory"""
        if not self.is_dir(name):
            raise NotADirectoryError(name)
        return next(dir_ for dir_ in self.child_directories if dir_.name.lower() == name.lower())


class VirtualFileSystem:
    def __init__(self,
                 artifacts_store_root: str,
                 default_username: str,
                 filesystem_template_path: str=FILESYSTEM_TEMPLATE,
                 lazy_load: bool=True):
        self.default_username = default_username
        self.user_home_path = win_path_join('c:\\users', self.default_username)
        self.currently_opened_files = dict()
        self.root_directory = VirtualDirectory('C:', artifacts_store_root)
        self.loaded_directories = dict({'c:': self.root_directory})
        self.lazy_load = lazy_load
        self.template = VirtualFileSystem.load_template(filesystem_template_path)
        self._load_filesystem_from_template_pickle(filesystem_template_path)

    @staticmethod
    def load_template( path: str):
        with open(path, 'rb') as fh:
            return pickle.load(fh)

    def _load_filesystem_from_template_pickle(self, path: str):
        for full_path in self.template:
            if self.lazy_load and full_path.count('\\') > 1:
                continue # on lazy mode -> initially load top level directories
            self._load_directory_from_template(full_path)

    def _load_directory_from_template(self, full_path: str) -> VirtualDirectory:
        normalized_full_path = self._template_user_home_to_fake_user_home(VirtualFileSystem.normalize_path(full_path))
        if normalized_full_path.lower() == 'c:':
            dir_ = self.root_directory
        else:
            parent_directory = self._load_directory_from_template_if_missing(win_path_dirname(normalized_full_path))
            dir_ = parent_directory.create_directory(win_path_basename(normalized_full_path))

        dirs, files = self.template[full_path]
        if normalized_full_path.lower() == 'c:\\users' and 'john' in dirs:
            dirs.remove('john') # rename user home
            dirs.append(self.default_username)

        # add sub directories and files from template
        for name in dirs:
            dir_.create_directory(name)
        for (file_name, size) in files:
            dir_.create_file(file_name, default_size=size)

        # store in cache
        self.loaded_directories[normalized_full_path.lower()] = dir_
        return dir_

    def _find_path_in_template(self, normalized_path):
        path = self._fake_user_home_to_template_user_home(normalized_path)
        return next((k for k in self.template if VirtualFileSystem.normalize_path(k).lower() == path), None)

    def _load_directory_from_template_if_missing(self, path) -> VirtualDirectory:
        normalized_path = VirtualFileSystem.normalize_path(path).lower()
        if normalized_path in self.loaded_directories:
            return self.loaded_directories[normalized_path] # path already loaded
        path_in_template = self._find_path_in_template(normalized_path)
        if not path_in_template:
            raise NotADirectoryError(f'{path_in_template} not found in template!')
        return self._load_directory_from_template(path_in_template)

    @staticmethod
    def normalize_path(path):
        return path.rstrip('\\')

    def _template_user_home_to_fake_user_home(self, path):
        template_user_home = 'c:\\users\\john'
        if not path.lower().startswith(template_user_home):
            return path
        return self.user_home_path + path[len(template_user_home):]

    def _fake_user_home_to_template_user_home(self, path):
        if not path.lower().startswith(self.user_home_path.lower()):
            return path
        return 'c:\\users\\john' + path[len(self.user_home_path):]

    def open(self, file_path: str) -> VirtualFile:
        """Open a file by path for r/w operations"""
        if file_path not in self.currently_opened_files:
            self.currently_opened_files[file_path] = self._open(file_path)
        return self.currently_opened_files[file_path]

    def _open(self, path: str) -> VirtualFile:
        parent_dir = win_path_dirname(path)
        self._load_directory_from_template_if_missing(parent_dir)
        dir_ = self.open_directory(parent_dir)
        return dir_.create_file(win_path_basename(path))

    def open_directory(self, path: str) -> VirtualDirectory:
        if not path.lower().startswith('c:'):
            raise NotADirectoryError(f'No such path {path}')

        def _open_dir_recursive(dir_: VirtualDirectory, path: List[str]) -> VirtualDirectory:
            if not len(path):
                return dir_
            return _open_dir_recursive(dir_.open_dir(path[0]), path[1:])

        return _open_dir_recursive(self.root_directory, path.rstrip('\\').split('\\')[1:])

    def listdir(self, path):
        """List directory by path"""
        self._load_directory_from_template_if_missing(path)
        dir_ = self.open_directory(path)
        return [d.name for d in dir_.child_directories], [(file_.name, file_.size) for file_ in dir_.child_files]

    def mkdir(self, path: str) -> VirtualDirectory:
        """Create a new directory"""
        self._load_directory_from_template_if_missing(win_path_dirname(path))
        parent_dir = win_path_dirname(path)
        name = win_path_basename(path)
        return self.open_directory(parent_dir).create_directory(name)

    def rmdir(self, path):
        raise NotImplementedError()

    def exists(self, path):
        """Check if a directory exists by path"""
        return self.is_dir(path) or self.is_file(path)

    def is_dir(self, path) -> bool:
        """Check if a path is an existing directory"""
        try:
            self._load_directory_from_template_if_missing(path)
            self.open_directory(path)
        except NotADirectoryError:
            return False
        return True

    def is_file(self, path) -> bool:
        """Check if a path is an existing file"""
        try:
            self._load_directory_from_template_if_missing(win_path_dirname(path))
            parent = self.open_directory(win_path_dirname(path))
            return parent.is_file(win_path_basename(path).lower())
        except NotADirectoryError:
            return False

    def remove(self, path):
        raise NotImplementedError()

    def rename_dir(self, old_path, new_name):
        raise NotImplementedError()
