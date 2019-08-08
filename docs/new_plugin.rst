Adding New PuppetRAT Plugin
===========================
The framework could be easily extended to support new RATs. If you wish to do so please create new Python file named after the RAT under the 'plugins' directory.
This file should contain at least one class which implements a new PuppetRAT, make sure to override both 'register' and 'loop' methods, example:

.. code-block:: python

    class MyRAT(PuppetRAT):
        def register(self):
            self._register(winapi.gethostname(),
                           winapi.get_volume_serial_number(),
                           self.vfs.user_home_path)

        def loop(self):
            while True:
                self._check_for_new_command()
                time.sleep(30)
