# MoP
## Overview
MoP ("Master of Puppets") is an open source framework for reverse engineers who wish to create and operate trackers for new malware found in the wild for research purpose.
To make it simple - MoP framework takes care of all the generic malware tracker stuff so the reverse engineer is left with pure reverse engineering work,
You only need to implement a simple plugin on top of MoP which describes the malware's network protocol.
MoP ships with a variety of workstation simulation capabilities, such as: fake filesystem manager, fake process manager, multi-worker orchestration, TOR integration and more.
All aiming to deceive adversaries into interacting with our simulated environment and possibly drop new unique samples.
Since everything is done in pure python, no virtual machines or Docker containers are needed and no actual malicious code is executed.
All of which enables us to scale up in a click of a button, connecting to potentially thousands of different malicious servers at once from a single instance running on a single laptop.
MoP framework comes with a number of pre-built plugins for known RATs, such as NjRAT and Gh0stRAT, Which have been showcased live at BlackHat Arsenal 2019!

## Use Cases
1. Collecting new variant of known malware (old school tracker approach):

Track few specific known malware for long time, fetch updates / new configuration.

2. Collect new malware samples (honypot-tracker hybrid approach):

Connect to many RAT clients(operators) simultaneously and start collecting unique dropped samples. 

3. War Games

Troll your red-team: serve funny "stolen" files, keylogging, etc... 

# Setup
```sh
git checkout https://github.com/intezer/mop && cd mop
pip3 install -r requirements.txt
orchestrator.py --target-ip X.X.X.X --target-port 5552 --plugin-name plugins.njrat.NjRAT 
```

# Targets Configuration
To add or remove targets you can simply create a new yaml file, follow the format:
```yaml
targets:
  <unique name 0>:
    ip: <ip>
    port: <port>
    plugin: <plugin>
  <unique name 1>:
    ip: <ip>
    port: <port>
    plugin: <plugin>
```

After you are done run the orchestrator in the following manner to make sure everything works:
```sh
orchestrator.py --targets-config <filename>
```

# PuppetRAT
The framework could be easily extended to support new RATs. If you wish to do so please create new Python file named after the RAT under the 'plugins' directory.
This file should contain at least one class which implements a new PuppetRAT, make sure to override both 'register' and 'loop' methods, example:
```python
class MyRAT(PuppetRAT):
    def register(self):
        self._register(winapi.gethostname(),
                       winapi.get_volume_serial_number(),
                       self.vfs.user_home_path)
        
    def loop(self):
        while True:
            self._check_for_new_command()
            time.sleep(30)
```

# Documentation
* TBD

# Dependencies
* Python 3

# Supported Platforms
MoP has been tested on Ubuntu 18.04 and Windows 10

## Supported RATs
* NjRAT(0.7d)
* Gh0stRAT(3.6)