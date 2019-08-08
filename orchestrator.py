#!/usr/bin/env python3.6
import argparse
import yaml
import importlib
import threading
import time
import random

from puppet_rat import PuppetRAT

from typing import List, Tuple


def import_puppet_rat(full_name: str) -> PuppetRAT:
    module_name, class_name = full_name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    if not module:
        raise ModuleNotFoundError(module_name)
    return getattr(module, class_name)


def connect(target_ip: str, target_port: int, plugin_name: str) -> None:
    thread = threading.Thread(target=_connect, args=(target_ip, target_port, plugin_name))
    thread.start()


def _connect(target_ip: str, target_port: int, plugin_name: str) -> None:
    rat_server = import_puppet_rat(plugin_name)
    server = rat_server(target_ip, target_port)
    while True:
        try:
            server.connect()
            server.register()
            server.loop()
        except:
            server.logger.exception('')
        time.sleep(random.randint(1, 30))


def connect_targets(targets: List[Tuple[str, Tuple[str, int, str]]]) -> None:
    for target_name, target in targets:
        print(f'[*] Connecting {target_name}...')
        connect(target['ip'], target['port'], target['plugin'])


def main():
    parser = argparse.ArgumentParser(description="=== [M]aster[O]f[P]uppets ===\r\nhttps://http://github.com/intezer/mop\r\nAdavnced Malware Tracking Framework",
                                     formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=1024))
    parser.add_argument('--target-ip', dest='target_ip', type=str, default=None, help='Target ip address to connect')
    parser.add_argument('--target-port', dest='target_port', type=int, default=None, help='Target port to connect')
    parser.add_argument('--plugin-name', dest='plugin_name', type=str, default=None,
                        help='Plugin to use, please specify full name(for example "plugins.njrat.NjRAT")')
    parser.add_argument('--targets-config', dest='targets_config', type=str, default=None, help='Config file with multiple targets')
    args = parser.parse_args()
    if args.target_ip:
        connect(args.target_ip, args.target_port, args.plugin_name)

    elif args.targets_config:
        with open(args.targets_config) as fh:
            config = yaml.load(fh, Loader=yaml.FullLoader)
            connect_targets(config['targets'].items())

    else:
        parser.error('No action requested, add --target-ip or --targets-config')


if __name__=='__main__':
    main()
