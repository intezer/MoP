Setup
=====
Setting up MoP is pretty strait forward, use following base commands to install the project using pip. Notice it requires Python >= 3.6.

.. code-block:: bash

    git checkout https://github.com/intezer/mop && cd mop
    pip3 install -r requirements.txt
    orchestrator.py --target-ip X.X.X.X --target-port 5552 --plugin-name plugins.njrat.NjRAT

If you wish the connect to multiple targets you may create a targets yaml file by the following format:

.. code-block:: yaml

    targets:
      <unique name 0>:
        ip: <ip>
        port: <port>
        plugin: <plugin>
      <unique name 1>:
        ip: <ip>
        port: <port>
        plugin: <plugin>

Usage example:

.. code-block:: bash

    orchestrator.py --targets-config targets.yaml