#!/usr/bin/env python3.6
import os
import socket
import socks
import base64
import yaml


def simple_b64_encode(data: str) -> str:
    return base64.b64encode(data.encode('ascii')).decode('ascii')


def safe_url(url: str) -> str:
    return url.replace('.', '[.]')


def parse_config(path):
    with open(path, 'rb') as fh:
        return yaml.load(fh, Loader=yaml.FullLoader)


def tcp_socket():
    """Create new tcp socket with proxy support depends on configuration"""
    config = parse_config(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'))
    use_proxy = 'proxy' in config and config['proxy']['use_proxy'] == True
    if use_proxy:
        s = socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, config['proxy']['ip'], config['proxy']['port'], True)
        return socks.socksocket()
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)