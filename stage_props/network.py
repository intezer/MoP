#!/usr/bin/env python3.6
import random
import ipaddress

from enum import Enum
from typing import NamedTuple, List

from stage_props.process_manager import process_by_name


class Proto(Enum):
    TCP = 0
    UDP = 1


class State(Enum):
    LISTENING = 0
    ESTABLISHED = 1


class Address(NamedTuple):
    ip: str
    port: int


class Connection(NamedTuple):
    proto: Proto
    local_address: Address
    foreign_address: Address
    state: State
    pid: int


def random_cdn_ip() -> str:
    def _random_cloudflare_ip() -> str:
        cloudflare_ranges = ['173.245.48.0/20',
                             '103.21.244.0/22',
                             '103.22.200.0/22',
                             '103.31.4.0/22',
                             '141.101.64.0/18',
                             '108.162.192.0/18',
                             '190.93.240.0/20',
                             '188.114.96.0/20',
                             '197.234.240.0/22',
                             '198.41.128.0/17',
                             '162.158.0.0/15',
                             '104.16.0.0/12',
                             '172.64.0.0/13',
                             '131.0.72.0/22'] # https://www.cloudflare.com/ips-v4
        return random.choice([str(ip) for ip in ipaddress.IPv4Network(random.choice(cloudflare_ranges))])
    return _random_cloudflare_ip()


def netstat(chrome_pid: int=None) -> List[Connection]:
    """Simulated output of `netstat -ob`. return a partiality randomized list of connections"""
    default_system_connections = [Connection(proto=Proto.TCP,
                                             local_address=Address('0.0.0.0', 139), # netbios
                                             foreign_address=Address('0.0.0.0', 0),
                                             state=State.LISTENING,
                                             pid=4), # System
                                  Connection(proto=Proto.TCP,
                                             local_address=Address('0.0.0.0', 445), # smb
                                             foreign_address=Address('0.0.0.0', 0),
                                             state=State.LISTENING,
                                             pid=4), # System
                                  Connection(proto=Proto.TCP,
                                             local_address=Address('0.0.0.0', 135), # rpc server
                                             foreign_address=Address('0.0.0.0', 0),
                                             state=State.LISTENING,
                                             pid=random.choice(process_by_name('svchost.exe')).pid)]

    if not chrome_pid:
        chrome_pid = random.randint(1000, 1999)
    for i in range(random.randint(2, 4)):
        default_system_connections.append(Connection(proto=Proto.TCP,
                                                     local_address=Address('127.0.0.1', random.randint(49151, 49999)),
                                                     foreign_address=Address(random_cdn_ip(), 443),
                                                     state=State.ESTABLISHED,
                                                     pid=chrome_pid))

    return default_system_connections
