#!/usr/bin/env python3
import unittest

import stage_props.process_manager


class TestProcessManager(unittest.TestCase):
    def test_pslist(self):
        self.assertIn('explorer.exe', [proc.name.lower() for proc in stage_props.process_manager.pslist()])

    def test_process_by_name(self):
        self.assertTrue(len(stage_props.process_manager.process_by_name('svchost.exe')) > 1)

    def test_process_by_pid(self):
        result = stage_props.process_manager.process_by_pid(4)
        self.assertTrue(result.name.lower() == 'system')
