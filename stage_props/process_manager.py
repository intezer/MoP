#!/usr/bin/env python3.6
import os
import csv
import random

from typing import NamedTuple, Generator, List

#
# This module generates a randomized view of processes based on a template csv file
# which was taken from a vm using `wmic process get Name,ProcessId,ParentProcessId,CommandLine /format:csv`

PSLIST_TEMPLATE = os.path.join(os.path.dirname(__file__), '..', 'resources', 'pslist.csv')


class Process(NamedTuple):
    pid: int
    ppid: int
    name: str
    cmdline: str


def pslist() -> Generator[Process, None, None]:
    """Retrieve a partiality randomized process list"""
    return _pslist_randomized()


def hide_chrome():
    return random.random() < 0.5


def number_of_svchosts():
    return random.randint(4, 12)


def _pslist_randomized() -> Generator[Process, None, None]:
    _hide_chrome = hide_chrome()
    _number_of_svchosts = number_of_svchosts()
    with open(PSLIST_TEMPLATE, 'r') as fh:
        reader = csv.DictReader(fh, fieldnames=['CommandLine', 'Name', 'ParentProcessId', 'ProcessId'], quotechar='"')
        next(reader) # skip header
        for row in reader:
            if row['Name'].lower().startswith('svchost'):
                if _number_of_svchosts == 0:
                    continue
                _number_of_svchosts -= 1
            elif row['Name'].lower().startswith('chrome') and _hide_chrome:
                continue
            yield Process(pid=int(row['ProcessId']),
                          ppid=int(row['ParentProcessId']),
                          name=row['Name'],
                          cmdline=row['CommandLine'])


def process_by_name(proces_name: str) -> List[Process]:
    """Get Process object by process name"""
    return [process for process in pslist() if process.name.lower() == proces_name.lower()]


def process_by_pid(pid: int) -> Process:
    """Get Process object by process id"""
    return next((process for process in pslist() if process.pid == pid), None)