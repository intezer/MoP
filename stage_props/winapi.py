#!/usr/bin/env python3
import os
import random
import PIL.Image
import io
import string

import stage_props.utils


def get_user_name() -> str:
    """Retrieve fake logged in user's username"""
    config = stage_props.utils.parse_config(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'))
    return random.choice(config['general']['usernames'])


def get_volume_serial_number() -> int:
    """Retrieve fake harddisk serial number"""
    return random.randint(0x10000000, 0xffffffff)


def random_desktop_screenshot():
    config = stage_props.utils.parse_config(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'))
    templates_path = config['screenshots']['templates']
    return os.path.join(templates_path, random.choice(os.listdir(templates_path)))


def capture_screen(width, height, format_='jpeg'):
    """Get a fake random desktop screenshot"""
    image = PIL.Image.open(random_desktop_screenshot())
    image.resize((width, height))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    buf = io.BytesIO()
    image.save(buf, format_)
    buf.seek(0)
    return buf.getvalue()


def gethostname() -> str:
    """Get a random hostname following WIN-XX convention"""
    return f'WIN-{"".join(random.choices(string.ascii_uppercase + string.digits, k=8))}'


def get_version_ex() -> bytes:
    """Win7SP1 Build 7601 raw OSVERSIONINFOA struct"""
    return b'\x20\x00\x00\x9c\x00\x00\x00\x06\x00\x00\x00\x01\x00\x00\x00\xb1\x1d\x00\x00\x02\x00\x00\x00\x53\x65\x72\x76\x69\x63\x65\x20\x50\x61\x63\x6b\x20\x31\x00\x00\x0c\x00\x00\x00\x98\xa1\x67\x00\x98\xa1\x67\x00\x93\xa1\x67\x00\x00\x00\x00\x00\xfe\xff\xff\x00\x00\x00\x67\x00\xbc\x56\xce\x01\x08\x55\xce\x00\x4b\x1a\x68\x73\x8c\x56\xce\x00\xcd\x1e\x10\x77\x06\x6b\x10\x00\xfe\xff\xff\xff\xa3\x3c\x0c\x77\xce\x3c\x0c\x77\x14\x02\x00\x00\x20\x02\x00\x00\x92\xa1\x67\x00\x90\xa1\x67\x00\x00\x00\x00\x00\x14\x02\x00\x00\x00\x00\x00\x00\x10\x08\x20\x90\x98\x55\xce\x00\x98\x55\xce\x00\x98\x56\xce\x00\x27\x2f\x6a\x73\x01\x00\x00\x00\x00\x03\x01\x00'
