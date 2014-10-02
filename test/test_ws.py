#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import unittest
import requests
import os
import json


class TestWebServices(unittest.TestCase):
    URL_BASE = "http://cbx-virtual.local:8888/api/homeautomation"
    SCENARIO_CFG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'home-automation-scenarios.cfg')

    @classmethod
    def setUpClass(cls):
        cls.test_data = json.load(file(cls.SCENARIO_CFG_FILE_PATH, 'rt'))

    def test01_get_scenarios(self):
        r = requests.get(self.URL_BASE + "/scenarios")
        self.assertEqual(r.status_code, 200)

        data = ReplyData(r.json())
        scenarios = data.scenarios
        self.assertListEqual(sorted([item['name'] for item in scenarios]), ['s01', 's02'])

    def test02_get_scenario_settings(self):
        r = requests.get(self.URL_BASE + "/scenario/s01/settings")
        self.assertEqual(r.status_code, 200)

        data = ReplyData(r.json())

        self.assertEqual(data.label, 'test scenario 01')
        actions = data.actions
        self.assertEqual(len(actions), 2)

        r = requests.get(self.URL_BASE + "/scenario/s42/settings")
        self.assertEqual(r.status_code, 404)

    def test04_execute_scenario(self):
        r = requests.get(self.URL_BASE + "/scenario/s01/execute")
        self.assertEqual(r.status_code, 200)


class ReplyData(object):
    def __init__(self, attrs):
        self.__dict__ = attrs


if __name__ == '__main__':
    unittest.main()
