Overview
================
MoP ("Master of Puppets") is an open source framework for reverse engineers who wish to create and operate trackers for new malware found in the wild for research purpose.
To make it simple - MoP framework takes care of all the generic malware tracker stuff so the reverse engineer is left with pure reverse engineering work, You only need to implement a simple plugin on top of MoP which describes the malware's network protocol.

MoP ships with a variety of workstation simulation capabilities, such as: fake filesystem manager, fake process manager, multi-worker orchestration, TOR integration and more. All aiming to deceive adversaries into interacting with our simulated environment and possibly drop new unique samples.

Since everything is done in pure python, no virtual machines or Docker containers are needed and no actual malicious code is executed. All of which enables us to scale up in a click of a button, connecting to potentially thousands of different malicious servers at once from a single instance running on a single laptop.

MoP framework comes with a number of pre-built plugins for known RATs, such as NjRAT and Gh0stRAT, Which have been showcased live at BlackHat Arsenal 2019!