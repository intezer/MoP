#!/usr/bin/env python3.6
import os
import socket
import random
import logging
import stage_props.utils


config = stage_props.utils.parse_config(os.path.join(os.path.dirname(__file__), 'config.yaml'))


class PuppetRAT:
    """
    MoP plugin base class.
    """
    def __init__(self, client_ip: str, client_port: int) -> None:
        self.client_ip = client_ip
        self.client_port = client_port
        self.pid = PuppetRAT._pid()
        self.logger = self._logger()
        self.conn = None

    def _logger(self) -> logging.Logger:
        logger = logging.getLogger(f'{self.__class__.__name__}_{self.client_ip}:{self.client_port}')
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        client_folder = os.path.join('artifacts', f'{self.client_ip}_{self.client_port}')
        PuppetRAT._mkdir(client_folder)
        file_handler = logging.FileHandler(os.path.join(client_folder, 'client.log'))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False
        logger.debug('logging started!')
        return logger

    @staticmethod
    def _mkdir(dir_):
        try:
            os.makedirs(dir_)
        except OSError:
            pass

    def connect(self):
        """Default implementation for simple TCP socket. Override this method if required"""
        self.conn = stage_props.utils.tcp_socket()
        self.conn.connect((self.client_ip, self.client_port))

    def register(self):
        """RAT's server registration. Please make sure to override this method"""
        raise NotImplementedError()

    def loop(self):
        """RAT's main loop. Please make sure to override this method"""
        raise NotImplementedError()

    @staticmethod
    def _pid():
        return random.randint(config['general']['random_rat_pid_min'], config['general']['random_rat_pid_max'])
