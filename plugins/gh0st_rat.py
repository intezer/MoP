#!/usr/bin/env python3
import os
import time
import struct
import zlib
import socket
import threading
import enum
import logging

import stage_props.winapi
import stage_props.filesystem
import stage_props.process_manager
from stage_props import utils

from typing import List

from puppet_rat import PuppetRAT


"""
    Packet Format:
        bPacketFlag('Gh0st') + nSize(int) + nUnCompressLength(int) + pData(zlib compressed data)
    
    LoginInfo Packet:
        bToken(0x66) + OsVerInfoEx(OSVERSIONINFOEX - 59 bytes) + CPUClockMhz(int) + IPAddress(IN_ADDR - 4 bytes) + HostName(char[50) + bIsWebCam(bool) + dwSpeed(DWORD)
"""


class Command(enum.Enum):
    """https://github.com/sincoder/gh0st/blob/master/common/macros.h#L19"""
    COMMAND_ACTIVED = 0
    COMMAND_LIST_DRIVE = enum.auto()
    COMMAND_LIST_FILES = enum.auto()
    COMMAND_DOWN_FILES = enum.auto()
    COMMAND_FILE_SIZE = enum.auto()
    COMMAND_FILE_DATA = enum.auto()
    COMMAND_EXCEPTION = enum.auto()
    COMMAND_CONTINUE = enum.auto()
    COMMAND_STOP = enum.auto()
    COMMAND_DELETE_FILE = enum.auto()
    COMMAND_DELETE_DIRECTORY = enum.auto()
    COMMAND_SET_TRANSFER_MODE = enum.auto()
    COMMAND_CREATE_FOLDER = enum.auto()
    COMMAND_RENAME_FILE = enum.auto()
    COMMAND_OPEN_FILE_SHOW = enum.auto()
    COMMAND_OPEN_FILE_HIDE = enum.auto()

    COMMAND_SCREEN_SPY = enum.auto()
    COMMAND_SCREEN_RESET = enum.auto()
    COMMAND_ALGORITHM_RESET = enum.auto()
    COMMAND_SCREEN_CTRL_ALT_DEL = enum.auto()
    COMMAND_SCREEN_CONTROL = enum.auto()
    COMMAND_SCREEN_BLOCK_INPUT = enum.auto()
    COMMAND_SCREEN_BLANK = enum.auto()
    COMMAND_SCREEN_CAPTURE_LAYER = enum.auto()
    COMMAND_SCREEN_GET_CLIPBOARD = enum.auto()
    COMMAND_SCREEN_SET_CLIPBOARD = enum.auto()

    COMMAND_WEBCAM = enum.auto()
    COMMAND_WEBCAM_ENABLECOMPRESS = enum.auto()
    COMMAND_WEBCAM_DISABLECOMPRESS = enum.auto()
    COMMAND_WEBCAM_RESIZE = enum.auto()
    COMMAND_NEXT = enum.auto()

    COMMAND_KEYBOARD = enum.auto()
    COMMAND_KEYBOARD_OFFLINE = enum.auto()
    COMMAND_KEYBOARD_CLEAR = enum.auto()

    COMMAND_AUDIO = enum.auto()

    COMMAND_SYSTEM = enum.auto()
    COMMAND_PSLIST = enum.auto()
    COMMAND_WSLIST = enum.auto()
    COMMAND_DIALUPASS = enum.auto()
    COMMAND_KILLPROCESS = enum.auto()
    COMMAND_SHELL = enum.auto()
    COMMAND_SESSION = enum.auto()
    COMMAND_REMOVE = enum.auto()
    COMMAND_DOWN_EXEC = enum.auto()
    COMMAND_UPDATE_SERVER = enum.auto()
    COMMAND_CLEAN_EVENT = enum.auto()
    COMMAND_OPEN_URL_HIDE = enum.auto()
    COMMAND_OPEN_URL_SHOW = enum.auto()
    COMMAND_RENAME_REMARK = enum.auto()
    COMMAND_REPLAY_HEARTBEAT = enum.auto()


class Token(enum.Enum):
    TOKEN_AUTH = 100
    TOKEN_HEARTBEAT = enum.auto()
    TOKEN_LOGIN = enum.auto()
    TOKEN_DRIVE_LIST = enum.auto()
    TOKEN_FILE_LIST = enum.auto()
    TOKEN_FILE_SIZE = enum.auto()
    TOKEN_FILE_DATA = enum.auto()
    TOKEN_TRANSFER_FINISH = enum.auto()
    TOKEN_DELETE_FINISH = enum.auto()
    TOKEN_GET_TRANSFER_MODE = enum.auto()
    TOKEN_GET_FILEDATA = enum.auto()
    TOKEN_CREATEFOLDER_FINISH = enum.auto()
    TOKEN_DATA_CONTINUE = enum.auto()
    TOKEN_RENAME_FINISH = enum.auto()
    TOKEN_EXCEPTION = enum.auto()

    TOKEN_BITMAPINFO = enum.auto()
    TOKEN_FIRSTSCREEN = enum.auto()
    TOKEN_NEXTSCREEN = enum.auto()
    TOKEN_CLIPBOARD_TEXT = enum.auto()

    TOKEN_WEBCAM_BITMAPINFO = enum.auto()
    TOKEN_WEBCAM_DIB = enum.auto()

    TOKEN_AUDIO_START = enum.auto()
    TOKEN_AUDIO_DATA = enum.auto()

    TOKEN_KEYBOARD_START = enum.auto()
    TOKEN_KEYBOARD_DATA = enum.auto()

    TOKEN_PSLIST = enum.auto()
    TOKEN_WSLIST = enum.auto()
    TOKEN_DIALUPASS = enum.auto()
    TOKEN_SHELL_START = enum.auto()


def loop_file_manager(ip, port):
    conn = stage_props.utils.tcp_socket()
    conn.connect((ip, port))
    FileManager(ClientSocket(conn))


def loop_system_manager(ip, port):
    conn = stage_props.utils.tcp_socket()
    conn.connect((ip, port))
    SystemManager(ClientSocket(conn))


class Manager:
    def __init__(self, client_socket: 'ClientSocket', logger: logging.Logger=None):
        self.client_socket = client_socket
        self.logger = logger if logger else logging.getLogger()

    def on_receive(self, buffer: bytes):
        raise NotImplementedError()


class KernelManager(Manager):
    def __init__(self, client_socket: 'ClientSocket', logger: logging.Logger=None):
        super(KernelManager, self).__init__(client_socket, logger)
        self.is_activated = False

    def on_receive(self, buffer: bytes):
        """https://github.com/sincoder/gh0st/blob/master/Server/svchost/common/KernelManager.cpp#L50"""
        self.logger.debug(buffer)
        if buffer[0] == Command.COMMAND_ACTIVED.value:
            self.is_activated = True

        elif buffer[0] == Command.COMMAND_LIST_DRIVE.value:
            file_manager_thread = threading.Thread(target=loop_file_manager, args=self.client_socket.conn.getpeername())
            file_manager_thread.start()

        elif buffer[0] == Command.COMMAND_SCREEN_SPY.value:
            self.logger.info('attacker tried to spy on your screen!')

        elif buffer[0] == Command.COMMAND_WEBCAM.value:
            self.logger.info('attacker tried to access the webcam!')

        elif buffer[0] == Command.COMMAND_AUDIO.value:
            self.logger.info('attacker tried to access the microphone!')

        elif buffer[0] == Command.COMMAND_SHELL.value:
            self.logger.info('attacker tried to open a shell!')

        elif buffer[0] == Command.COMMAND_KEYBOARD.value:
            self.logger.info('attacker tried to get keystrokes logging!')

        elif buffer[0] == Command.COMMAND_SYSTEM.value:
            system_manager_thread = threading.Thread(target=loop_system_manager, args=self.client_socket.conn.getpeername())
            system_manager_thread.start()

        elif buffer[0] == Command.COMMAND_DOWN_EXEC.value:
            url = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker tried to download & execute! url: {utils.safe_url(url)}')

        elif buffer[0] == Command.COMMAND_OPEN_URL_SHOW.value:
            return

        elif buffer[0] == Command.COMMAND_OPEN_URL_HIDE.value:
            return

        elif buffer[0] == Command.COMMAND_REMOVE.value:
            self.logger.warn('attacker tried to uninstall the server!')

        elif buffer[0] == Command.COMMAND_CLEAN_EVENT.value:
            self.logger.info('attacker tried clear the logs!')

        elif buffer[0] == Command.COMMAND_SESSION.value:
            self.shutdown_windows(buffer[1])

        elif buffer[0] == Command.COMMAND_RENAME_REMARK.value:
            name = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker renamed the server to "{name}"!')

        elif buffer[0] == Command.COMMAND_UPDATE_SERVER.value:
            url = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker tried to update! url: {utils.safe_url(url)}')

        elif buffer[0] == Command.COMMAND_REPLAY_HEARTBEAT.value:
            return

        else:
            self.logger.warn(f'unknown command "{hex(buffer[0])}"')

    def shutdown_windows(self, reason):
        shutdown_type = 'unknown'
        if reason == 0 or reason == 4:
            shutdown_type = 'logoff'
        elif reason == 1 or reason == 5:
            shutdown_type = 'shutdown'
        elif reason == 2 or reason == 6:
            shutdown_type = 'reboot'
        self.logger.info(f'attacker tried to {shutdown_type} the system!')


class ClientSocket:
    """
    https://github.com/sincoder/gh0st/Server/svchost/ClientSocket.cpp
    """
    PACKET_FLAG = b'Gh0st' # https://github.com/sincoder/gh0st/Server/svchost/ClientSocket.cpp#L31
    MAX_RECV_BUFFER = 1024 * 8 # https://github.com/sincoder/gh0st/blob/master/common/macros.h#L117

    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.manager = None

    def connect(self) -> None:
        work_thread = threading.Thread(target=ClientSocket.work_thread, args=(self,))
        work_thread.start()

    def send(self, data: bytes) -> None:
        compressed_data = zlib.compress(data)
        size = len(ClientSocket.PACKET_FLAG) + 8 + len(compressed_data)
        packet = ClientSocket.PACKET_FLAG + struct.pack('ii', size, len(data)) + compressed_data
        self.conn.send(packet)

    @staticmethod
    def work_thread(client_socket: 'ClientSocket') -> None:
        while True:
            try:
                raw_data = client_socket.conn.recv(ClientSocket.MAX_RECV_BUFFER)
                client_socket.on_read(raw_data)
            except ConnectionResetError:
                return

    def on_read(self, raw_data: bytes) -> None:
        if len(raw_data):
            self.manager.on_receive(zlib.decompress(raw_data[len(ClientSocket.PACKET_FLAG) + 8:]))

    def set_manager_callback(self, manager: Manager) -> None:
        """https://github.com/sincoder/gh0st/blob/master/Server/svchost/ClientSocket.cpp#L479"""
        self.manager = manager


class FileManager(Manager):
    """https://github.com/sincoder/gh0st/blob/master/Server/svchost/common/FileManager.cpp"""
    def __init__(self, client_socket: ClientSocket, logger: logging.Logger=None):
        super(FileManager, self).__init__(client_socket, logger)
        client_ip, client_port = client_socket.conn.getpeername()
        self.logged_in_user = stage_props.winapi.get_user_name()
        self.current_process_filename = None
        vfs_root = os.path.join(os.path.dirname(__file__), '..', 'artifacts', f'{client_ip}_{client_port}')
        self.vfs = stage_props.filesystem.VirtualFileSystem(vfs_root, self.logged_in_user)
        self.send_drive_list()
        self.client_socket.set_manager_callback(self)
        self.client_socket.connect()

    def on_receive(self, buffer):
        self.logger.debug(str(buffer))
        if buffer[0] == Command.COMMAND_LIST_FILES.value:
            dir_ = buffer[1:-1].decode(errors='ignore')
            self.send_files_list(dir_)

        elif buffer[0] == Command.COMMAND_DELETE_FILE.value or buffer[0] == Command.COMMAND_DELETE_DIRECTORY.value:
            path = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker tried to delete {path}')
            self.send_token(Token.TOKEN_DELETE_FINISH)

        elif buffer[0] == Command.COMMAND_DOWN_FILES.value:
            path = buffer[1:].decode(errors='ignore')
            self.logger.info(f'attacker tried to steal file ({str(path)})!')
            self.upload_to_remote(path)

        elif buffer[0] == Command.COMMAND_CONTINUE.value:
            self.send_file_data(struct.unpack('L', buffer[1:])[0])

        elif buffer[0] == Command.COMMAND_CREATE_FOLDER.value:
            path = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker tried to create {path}!')
            self.vfs.mkdir(path)
            self.send_token(Token.TOKEN_CREATEFOLDER_FINISH)

        elif buffer[0] == Command.COMMAND_RENAME_FILE.value:
            path = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker tried to rename {path}!')
            self.send_token(Token.TOKEN_RENAME_FINISH)

        elif buffer[0] == Command.COMMAND_STOP.value:
            self.logger.info(f'attacker stopped file transfer')
            self.send_token(Token.TOKEN_TRANSFER_FINISH)

        elif buffer[0] == Command.COMMAND_SET_TRANSFER_MODE.value:
            raise NotImplementedError()

        elif buffer[0] == Command.COMMAND_FILE_SIZE.value:
            filename = buffer[9:-1].decode(errors='ignore')
            self.logger.info(f'attacker created the file {filename}!')
            self.create_local_recv_file(filename)

        elif buffer[0] == Command.COMMAND_FILE_DATA.value:
            offset_high, offset_low = struct.unpack('II', buffer[1:9])
            self.write_local_recv_file(offset_high, offset_low, buffer[9:])

        elif buffer[0] == Command.COMMAND_OPEN_FILE_SHOW.value:
            path = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker opened visible file {path}!')

        elif buffer[0] == Command.COMMAND_OPEN_FILE_HIDE.value:
            path = buffer[1:-1].decode(errors='ignore')
            self.logger.info(f'attacker opened hidden file {path}!')

        else:
            self.logger.warn(f'unknown file manager command {str(buffer[0])}')

    def send_drive_list(self) -> None:
        self.client_socket.send(bytes([Token.TOKEN_DRIVE_LIST.value]) +
                                b'C\x03\xfdO\x00\x00\x07\x16\x00\x00Local Disk\x00NTFS\x00')

    def send_files_list(self, dir_: str) -> None:
        directories, files = self.vfs.listdir(dir_)
        files_list = bytes([Token.TOKEN_FILE_LIST.value])
        for item in directories + files:
            files_list += b'\x00' if item in files else b'\x10'
            files_list += (item[0].encode() if item in files else item.encode()) + b'\x00'
            last_write = 0
            files_list += struct.pack('LL', item[1] if item in files else 0, last_write)
        self.client_socket.send(files_list)

    def create_local_recv_file(self, filename) -> None:
        """https://github.com/sincoder/gh0st/blob/master/Server/svchost/common/FileManager.cpp#L588"""
        self.current_process_filename = filename
        self.get_file_data()

    def write_local_recv_file(self, offset_high: int, offset_low: int, data: bytes):
        if not self.current_process_filename:
            return
        local_file = self.vfs.open(self.current_process_filename)
        local_file.append(data)
        local_file.close()
        self.client_socket.send(bytes([Token.TOKEN_DATA_CONTINUE.value]) + struct.pack('II', offset_high, offset_low + len(data)))

    def send_token(self, token: Token) -> None:
        self.client_socket.send(bytes([token.value]))

    def upload_to_remote(self, local_path: str) -> None:
        self.send_token(Token.TOKEN_TRANSFER_FINISH)

    def send_file_data(self, size: int) -> None:
        return

    def get_file_data(self):
        self.client_socket.send(bytes([Token.TOKEN_DATA_CONTINUE.value]) + b'\x00' * 8)


class SystemManager(Manager):
    """https://github.com/sincoder/gh0st/blob/master/Server/svchost/common/SystemManager.cpp"""

    def __init__(self, client_socket: ClientSocket, logger: logging.Logger = None):
        super(SystemManager, self).__init__(client_socket, logger)
        self.client_socket.set_manager_callback(self)
        self.client_socket.connect()
        self.send_process_list()

    def on_receive(self, buffer):
        self.logger.debug(str(buffer))
        if buffer[0] == Command.COMMAND_PSLIST.value:
            self.send_process_list()

        elif buffer[0] == Command.COMMAND_WSLIST.value:
            return

        elif buffer[0] == Command.COMMAND_KILLPROCESS.value:
            self.logger.info(f'attacker tried to kill pid {struct.unpack("I", buffer[1:])}')

    def send_process_list(self) -> None:
        self.client_socket.send(self.get_process_list())

    def get_process_list(self) -> bytes:
        """https://github.com/sincoder/gh0st/blob/master/Server/svchost/common/SystemManager.cpp#L125"""
        buf = b''
        for process in stage_props.process_manager.pslist():
            buf += struct.pack('I', process.pid) + process.name.encode('ascii') + b'\x00\x00'
        return bytes([Token.TOKEN_PSLIST.value]) + buf


class Gh0stRAT(PuppetRAT):
    def register(self):
        self.client_socket = ClientSocket(self.conn)
        manager = KernelManager(self.client_socket, self.logger)
        self.client_socket.set_manager_callback(manager)
        self.client_socket.connect()
        self.send_login_info()

    def send_login_info(self):
        """https://github.com/sincoder/gh0st/blob/f434b0df9d08540c8d81d82892def50198aa8849/Server/svchost/common/login.h#L177"""
        self.client_socket.send(struct.pack('c159si4s50sHI',
                                            bytes([Token.TOKEN_LOGIN.value]),
                                            stage_props.winapi.get_version_ex(),
                                            2592, # CPUClockMhz
                                            socket.inet_aton('192.168.143.1'),
                                            stage_props.winapi.gethostname().encode(),
                                            False, # bIsWebCam
                                            0))

    def loop(self):
        while True:
            time.sleep(1.0)
