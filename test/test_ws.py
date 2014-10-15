#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import unittest
import requests
import os
import json


class TestWebServices(unittest.TestCase):
    """ WARNING

    These tests are not really pure unit tests since they use a running CSTBox to be executed.
    """
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
        self.assertListEqual(sorted([id_ for id_, _ in scenarios]), ['s01', 's02'])

    def test02_get_scenario_settings(self):
        r = requests.get(self.URL_BASE + "/scenario/s01/settings")
        self.assertEqual(r.status_code, 200)

        data = ReplyData(r.json())

        self.assertEqual(data.label, 'test scenario 01')
        actions = data.actions
        self.assertEqual(len(actions), 2)

        r = requests.get(self.URL_BASE + "/scenario/s42/settings")
        self.assertEqual(r.status_code, 404)

    def test03_set_scenario_settings(self):
        url = self.URL_BASE + "/scenario/s01/settings"
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)

        data = ReplyData(r.json())
        saved_label = data.label
        data.label = new_label = 'modified test scenario 01'

        r = requests.post(url, data=json.dumps(data.__dict__))
        self.assertEqual(r.status_code, 200)

        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        data = ReplyData(r.json())
        self.assertEqual(data.label, new_label)

        data.label = saved_label
        r = requests.post(url, data=json.dumps(data.__dict__))
        self.assertEqual(r.status_code, 200)
        r = requests.get(url)
        self.assertEqual(r.status_code, 200)
        data = ReplyData(r.json())
        self.assertEqual(data.label, saved_label)

    def test04_add_remove_scenario_settings(self):
        url = self.URL_BASE + "/scenario/s01/settings"
        r = requests.get(url)

        data = ReplyData(r.json())
        data.label = 'copy of ' + data.label
        r = requests.put(self.URL_BASE + "/scenario/s03/settings", data=json.dumps(data.__dict__))
        self.assertEqual(r.status_code, 200)

        r = requests.get(self.URL_BASE + "/scenario/s03/settings", data=json.dumps(data.__dict__))
        self.assertEqual(r.status_code, 200)

        r = requests.delete(self.URL_BASE + "/scenario/s03/settings")
        self.assertEqual(r.status_code, 200)

        url = self.URL_BASE + "/scenario/s03/settings"
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)

    def test10_execute_scenario(self):
        r = requests.get(self.URL_BASE + "/scenario/s01/execute")
        self.assertEqual(r.status_code, 200)


class ReplyData(object):
    def __init__(self, attrs):
        self.__dict__ = attrs


if __name__ == '__main__':
    unittest.main()
