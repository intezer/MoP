import os
import getpass
import pickle
import argparse
"""
Utility to create a filesystem template file from current Windows machine
"""

IGNORE = [os.path.dirname(__file__).lower(),
          'mop',
          'vmware',
          'wireshark',
          'npcap',
          'ida',
          'python',
          '.py',
          'process hacker',
          'sandboxie',
          'resource hacker',
          'cff',
          'olly',
          'pestudio',
          'sysinternals']


def ignore_path(path):
    path_lowercase = path.lower()
    return any(x for x in IGNORE if x in path_lowercase)


def map_filesystem():
    out = dict()
    real_username = getpass.getuser()
    for root, dirs, files in os.walk('c:\\'):
        if ignore_path(root):
            print('ignoring ' + root + '...')
            continue
        try:
            out[root.replace(real_username, 'john')] = ([dir_.replace(real_username, 'john') for dir_ in dirs if not ignore_path(dir_)],
                                                        [(file_.replace(real_username, 'john'), os.stat(os.path.join(root, file_)).st_size) for file_ in files if not ignore_path(file_)])
        except WindowsError:
            print(root + ' failed!')
    return out

def main():
    parser = argparse.ArgumentParser(description="https://http://github.com/intezer/mop")
    parser.add_argument('--out', dest='output', type=str, help='output filename')
    args = parser.parse_args()
    if args.output:
        with open(args.output, 'wb') as fh:
            pickle.dump(map_filesystem(), fh)
    else:
        parser.error('no output filename!')


if __name__ == '__main__':
    main()