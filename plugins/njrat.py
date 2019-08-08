#!/usr/bin/env python3.6
import os
import base64
import gzip
import io
import random
import string

import stage_props.winapi as winapi
import stage_props.network as network
import stage_props.process_manager as process_manager
import stage_props.utils as utils
import stage_props.filesystem as filesystem

from datetime import datetime
from enum import Enum

from puppet_rat import PuppetRAT

DEFAULT_FM_DIRS = ['C:\\*Fixed', 'C:\\Users\\<user>\\Desktop\\*', 'C:\\Users\\<user>\\Pictures\\*',
                   'C:\\Users\\<user>\\*',
                   'C:\\Users\\<user>\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\*',
                   'C:\\Program Files\\*', 'C:\\ProgramData\\*', 'C:\\Windows\\*',
                   'C:\\Windows\\system32\\*', 'C:\\Users\\<user>\\AppData\\Roaming\\*',
                   'C:\\Users\\<user>\\AppData\\Local\\Temp\\*']

SYSTEM_PROCESSES = ['csrss.exe',
                    'dwn.exe',
                    'explorer.exe',
                    'lsass.exe',
                    'lsm.exe',
                    'dllhost.exe',
                    'GoogleUpdate.exe',
                    'msdtc.exe',
                    'smss.exe',
                    'services.exe',
                    'svchost.exe',
                    'System',
                    'winlogon.exe',
                    'System Idle Process',
                    'WmiPrvSE.exe']


class NjRAT(PuppetRAT):
    SERVER_VERSION = '0.7d'
    class FileManagerCommand(Enum):
        FM_LIST_CWD = '~'
        FM_LIST_DIRS = '!'
        FM_LIST_FILES = '@'
        FM_UPLOAD = 'up'
        FM_DOWNLOAD = 'dw'
        FM_RUN = 'rn'

    def __init__(self, client_ip: str, client_port: int) -> None:
        super(NjRAT, self).__init__(client_ip, client_port)
        self.logged_in_user = winapi.get_user_name()
        self.volume_serial = winapi.get_volume_serial_number()
        vfs_root = os.path.join(os.path.dirname(__file__), '..', 'artifacts', f'{client_ip}_{client_port}')
        self.vfs = filesystem.VirtualFileSystem(vfs_root, self.logged_in_user)
        self._add_interesting_files_to_vfs()
        self.screenshot = None

    def __del__(self):
        self.conn.close()

    def _add_interesting_files_to_vfs(self):
        for filename, size in [('passwords.txt', random.randint(512, 1024)),
                               ('classified.pdf', random.randint(1024 * 100, 1024 * 1000))]:
            fh = self.vfs.open(f'{self.vfs.user_home_path}\\desktop\\{filename}')
            fh.write(b'\x00' * size)
            fh.close()

    def send(self, msg: str):
        raw_msg = f'{len(msg)}\x00{msg}'
        self.logger.debug(f'sending msg "{raw_msg}"')
        self.conn.send(raw_msg.encode('ascii'))

    def send_bytes(self, msg: bytes):
        self.conn.send(str(len(msg)).encode() + b'\x00' + msg)

    def recv(self):
        raw = self.conn.recv(1024)
        s, msg = raw.split(b'\x00', 1)
        s = int(s)
        while s > len(msg):
            msg = msg + self.conn.recv(1024)
        return msg

    def register(self):
        self._register(winapi.gethostname(),
                       datetime.now().strftime('%y-%m-%d'),
                       'Win 7 Ultimate SP1 x86',
                       'chrome.exe')

    def loop(self):
        while True:
            msg = self.recv()
            self.logger.debug(f'received msg "{msg}"')
            if not len(msg):
                self._ping()
            else:
                self._handle_msg(msg)


    def _register(self, computer_name, date, os_version, active_window):
        """https://github.com/mwsrc/njRAT/blob/539aa13375473d9c9bf74e81e65bb34bdb348a30/njRAT/Stub/OK.VB#L993"""

        self.send(f'll|\'|\'|{self.victim_id}|\'|\'|{computer_name}|\'|\'|{self.logged_in_user}|\'|'
                  f'\'|{date}|\'|\'||\'|\'|{os_version}|\'|\'|No|\'|\'|{self.SERVER_VERSION}|\'|\'|..'
                  f'|\'|\'|{base64.b64encode(active_window.encode("utf-8"))}|\'|\'|')

    @property
    def victim_id(self) -> str:
        return base64.b64encode('HacKed_{:08X}'.format(self.volume_serial).encode()).decode()

    def _send_screenshot(self, width, height):
        if not self.screenshot:
            self.screenshot = winapi.capture_screen(min(int(width), 512),
                                                                min(int(height), 512))
        self.send_bytes(b'CAP|\'|\'|' + self.screenshot)

    def _send_default_directories_list(self):
        def get_default_directories_list(fake_username):
            for dir_ in DEFAULT_FM_DIRS:
                yield dir_.replace('<user>', fake_username)

        fake_username = self.logged_in_user
        b64_fake_dirs = '|\'|\'|'.join([base64.b64encode(dir_.encode('utf-8')).decode('ascii') for dir_ in get_default_directories_list(fake_username)])
        self.send(f'FM|\'|\'|!|\'|\'|{b64_fake_dirs}')

    def _send_fake_directories_list(self, path):
        fake_directories_list = self.listdir(path)
        b64_path = utils.simple_b64_encode(path)
        if fake_directories_list and fake_directories_list[0]:
            formatted_results = '*'.join([utils.simple_b64_encode(d) for d in fake_directories_list[0]])
            self.send(f'FM|\'|\'|@|\'|\'|{b64_path}|\'|\'|{formatted_results}*')
        else:
            self.send(f'FM|\'|\'|@|\'|\'|{b64_path}|\'|\'|')

    def _send_fake_files_list(self, path):
        fake_files_list = self.listdir(path)
        b64_path = utils.simple_b64_encode(path)
        if fake_files_list and fake_files_list[1]:
            formatted_results = "*".join([utils.simple_b64_encode(f'{fname}*{size}') for fname, size in fake_files_list[1]])
            self.send(f'FM|\'|\'|#|\'|\'|{b64_path}|\'|\'|{formatted_results}*')
        else:
            self.send(f'FM|\'|\'|#|\'|\'|{b64_path}|\'|\'|')

    def listdir(self, path):
        try:
            return self.vfs.listdir(path)
        except NotADirectoryError:
            return None

    def _receive_file(self, file_id: str, filename: str, size: int):
        data = self._receive_file_content(file_id, filename, size)
        file_ = self.vfs.open(filename)
        file_.write(data)
        self.logger.info(f'file saved! {file_.sha256}')
        file_.close()
        self._ping()

    def _receive_file_content(self, file_id: str, filename: str, size: int):
        msg = f'get|\'|\'|{file_id}|\'|\'|{utils.simple_b64_encode(filename)}'
        conn = utils.tcp_socket()
        conn.connect((self.client_ip, self.client_port))
        conn.send(f'{len(msg)}\x00{msg}'.encode('utf-8'))
        content = b''
        while len(content) < int(size):
            content = content + conn.recv(1024)
        conn.close()
        return content

    def _handle_file_manager_request(self, msg):
        def parse_path():
            path = base64.b64decode(msg.split(b'|\'|\'|')[3])
            self.logger.info(f'attacker asked for "{path.decode()}" files listing')
            return path.decode('ascii')

        params = msg.split(b'|\'|\'|')[2].decode()
        if params == NjRAT.FileManagerCommand.FM_LIST_CWD.value:
            self._send_default_directories_list()

        elif params == NjRAT.FileManagerCommand.FM_LIST_DIRS.value:
            self._send_fake_directories_list(parse_path())

        elif params == NjRAT.FileManagerCommand.FM_LIST_FILES.value:
            self._send_fake_files_list(parse_path())

        elif params == NjRAT.FileManagerCommand.FM_UPLOAD.value:
            file_id, filename, size = msg.split(b'|\'|\'|')[3:6]
            filename = base64.b64decode(filename)
            self.logger.info(f'attacker tries to upload a file! {filename}')
            self._receive_file(file_id.decode('ascii'), filename.decode('ascii'), int(size))

        elif params == NjRAT.FileManagerCommand.FM_DOWNLOAD.value:
            self.logger.info(f'attacker tried to download "{parse_path()}"')

        elif params == NjRAT.FileManagerCommand.FM_RUN.value:
            self.logger.info(f'attacker tried to run "{parse_path()}"')

        else:
            self.logger.warn(f'unknown file manager params "{params}"')

    def _handle_msg(self, msg):
        if msg.startswith(b'CAP'):
            _, width, height = msg.split(b'|\'|\'|')
            self._send_screenshot(width, height)

        elif msg.startswith(b'Ex'):
            _, plugin, params = msg.split(b'|\'|\'|')[:3]

            # right click -> manager -> file manager
            if plugin == b'fm':
                self._handle_file_manager_request(msg)

            # right click ->manager -> process manager
            elif plugin == b'proc':
                self._handle_process_manager_request(msg)

            # right click -> manager -> connections
            elif plugin == b'tcp':
                self._handle_connections_request(params)

            # right click -> manager -> remote shell
            elif plugin == b'rs':
                if params == b'~':
                    cmd_exe_banner = ["Microsoft Windows [Version 6.1.7601]",
                                      "Copyright (c) 2009 Microsoft Corporation.  All rights reserved.", ""]
                    self.send('rss')
                    for line in [base64.b64encode(x.encode()) for x in cmd_exe_banner]:
                        self.send(f'rs|\'|\'|{line.decode()}')

                elif params == b'!':
                    cmdline = base64.b64decode(msg.split(b'|\'|\'|')[-1])
                    self.logger.info(f'attacker tried to execute: {cmdline}')
                    b64_cmd_echo = base64.b64encode(f'c:\\fake>{cmdline}'.encode())
                    self.send(f'rs|\'|\'|{b64_cmd_echo}')

                else:
                    self.logger.warn(f'unknown remote shell params {params}')
            else:
                self.logger.warn(f'unknown plugin({plugin})')

        elif msg.startswith(b'PLG'):
            self.logger.info('attacker tried to install plugin!')

        # right click -> server -> upgrade
        elif msg.startswith(b'up'):
            self.logger.info('attacker tried to upgrade server!')
            raw = msg.split(b'|\'|\'|')[1]
            if self._is_gzip(raw):
                data = self._decompress_gzip(raw)
                random_filename = "".join(random.choices(string.ascii_letters, k=8))
                path = f'c:\\users\\{self.logged_in_user}\\appdata\\local\\temp\\{random_filename}'
                file_ = self.vfs.open(path)
                file_.write(data)
                self.logger.info(f'file saved!: {file_.sha256}')
                file_.close()
            else:
                self.logger.info(f'url of upgrade binary: {utils.safe_url(raw.decode())}')

        # right click -> keylogger
        elif msg.startswith(b'kl'):
            self.logger.info('attacker asked for keystroke log!')
            today = datetime.now().strftime("%y-%m-%d")
            fake_keystroke_log = f'\r\n\x01{today} chrome New Tab - Google Chrome\x01\r\n' \
                                 f'googl.[Back]e.com[ENTER]' \
                                 f'What is MoP Framework?[ENTER]' \
                                 f'\r\n\x01{today} Outlook.exe - Mr.Victim\x01\r\n' \
                                 f'sec@my[Back]corporate.com' \
                                 f'Hi,[ENTER][ENTER]Did anyone heard on this MoP thing?[ENTER]'
            b64_fake_banner = base64.b64encode(fake_keystroke_log.encode())
            self.send(f'kl|\'|\'|{b64_fake_banner.decode()}')

        elif msg.startswith(b'rn'):
            raw, mode, payload = msg.split(b'|\'|\'|')[:3]

            if mode == b'exe':
                if self._is_gzip(payload):
                    data = self._decompress_gzip(payload)
                    random_filename = "".join(random.choices(string.ascii_letters, k=8))
                    path = f'c:\\users\\{self.logged_in_user}\\appdata\\local\\temp\\{random_filename}'
                    file_ = self.vfs.open(path)
                    file_.write(data)
                    self.logger.info(f'file saved!: {file_.sha256}')
                    file_.close()
                else:
                    self.logger.info(f'url: {payload.decode()}')
            else:
                data = self._decompress_gzip(payload)
                try:
                    data = data.decode()
                except:
                    pass
                self.logger.info(f'attacker tried to execute a script: {data} type: {mode}')
        else:
            self.logger.warn(f'unknown command "{msg}"')

    @staticmethod
    def _decompress_gzip(data):
        bytes_io = io.BytesIO()
        bytes_io.write(data)
        bytes_io.seek(0)
        _file = gzip.GzipFile(fileobj=bytes_io)
        return _file.read()

    @staticmethod
    def _is_gzip(data: bytes) -> bool:
        return data.startswith(b'\x1f\x8b')

    def _handle_connections_request(self, params):
        if params == b'~':
            connections = list()
            if not hasattr(self, 'netstat'):
                self.netstat = network.netstat()

            for connection in self.netstat:
                proc = process_manager.process_by_pid(connection.pid)
                connections.append(f'{connection.local_address.ip}:{connection.local_address.port},'
                                   f'{connection.foreign_address.ip}:{connection.foreign_address.port},2,'
                                   f'{connection.pid}'
                                   f'[{proc.name if proc else "chrome.exe"}]')

            self.send(f'tcp|\'|\'|~|\'|\'|{"*".join(connections)}')
            self.send('tcp|\'|\'|RM|\'|\'|')
        else:
            self.logger.warn(f'unknown connections params "{params}"')

    def _ping(self):
        self.send('')

    def _handle_process_manager_request(self, raw_msg):
        params = raw_msg.split(b'|\'|\'|')[2]
        if params == b'~':
            self.send(f'proc|\'|\'|pid|\'|\'|{self.pid}')

        # process list
        elif params == b'U':
            if raw_msg.endswith(b'U'):
                data = ""
                for proc in process_manager.pslist():
                    owner = self.logged_in_user if proc.name not in SYSTEM_PROCESSES else ''
                    data += '[:]'.join([proc.name, str(proc.pid), '', owner, proc.cmdline])
                    data += '[::]'
                self.send(f'proc|\'|\'|!|\'|\'|{data}')
            else:
                self.send('proc|\'|\'|!|\'|\'|')
            self.send('proc|\'|\'|RM')
        else:
            self.logger.warn(f'unknwon process list params "{params}"')
