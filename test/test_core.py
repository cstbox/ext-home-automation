#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import unittest
import os.path
import json

from pycstbox.log import Loggable
from pycstbox.homeautomation.core import Scenario, BasicAction, ScenariosManager


class BaseTestCase(unittest.TestCase, Loggable):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        Loggable.__init__(self)

    def setUp(self):
        self.logger.name = self.id().split('.')[-1]
        self.log_info('----- START -----')

    def tearDown(self):
        self.log_info('------ END ------')


class TestScenario(BaseTestCase):
    def setUp(self):
        super(TestScenario, self).setUp()
        self.evtmgr = MockUpEventManager()
        self.scenario = Scenario('scenario 1')

    def test01_execute_action(self):
        action = BasicAction('switch', 'kitchen', 1)
        action.execute(self.evtmgr)
        self.assertEqual(self.evtmgr.last_event, ('switch', 'kitchen', 1))

    def test02_add_action(self):
        self.scenario.add_action(BasicAction('switch', 'kitchen', 1))
        self.scenario.execute(self.evtmgr)
        self.assertEqual(self.evtmgr.last_event, ('switch', 'kitchen', 1))

    def test03_sequence(self):
        self.scenario.add_action(BasicAction('switch', 'kitchen', 0))
        self.scenario.add_action(BasicAction('switch', 'living', 0))
        self.scenario.add_action(BasicAction('switch', 'bedroom', 1))
        self.scenario.execute(self.evtmgr)
        self.assertEqual(self.evtmgr.last_event, ('switch', 'bedroom', 1))
        self.assertEqual(self.evtmgr.events_count, 3)

    def test04_query(self):
        self.scenario.add_action(BasicAction('switch', 'kitchen', 0))
        self.scenario.add_action(BasicAction('switch', 'living', 0))
        self.scenario.add_action(BasicAction('dim', 'bedroom', 50))

        self.log_info('Scenario sequence:')
        for action in self.scenario.actions:
            self.log_info("- %s" % action.label)

    def test05_as_dict(self):
        self.scenario.add_action(BasicAction('switch', 'kitchen', 0))
        self.scenario.add_action(BasicAction('switch', 'living', 0))
        self.scenario.add_action(BasicAction('dim', 'bedroom', 50))

        d = self.scenario.as_dict()
        self.assertEqual(d['label'], 'scenario 1')
        self.assertEqual(len(d['actions']), 3)

    def test06_from_dict(self):
        d = {
            "label": "test scenario 01",
            "actions": [
                {"label": "switch off living lights", "verb": "switch", "target": "living", "data": 0},
                {"label": "dim bedroom lights", "verb": "dim", "target": "bedroom", "data": 50}
            ]
        }
        s = Scenario.from_dict(d)
        self.assertEqual(s.label, 'test scenario 01')
        self.assertEqual(len(s.actions), 2)

    def test07_update(self):
        self.assertEqual(self.scenario.label, 'scenario 1')
        self.assertEqual(len(self.scenario.actions), 0)

        d = {
            "label": "test scenario 01",
            "actions": [
                {"label": "switch off living lights", "verb": "switch", "target": "living", "data": 0},
                {"label": "dim bedroom lights", "verb": "dim", "target": "bedroom", "data": 50}
            ]
        }
        self.scenario.update(d)
        self.assertEqual(self.scenario.label, 'test scenario 01')
        self.assertEqual(len(self.scenario.actions), 2)


class TestScenariosManager(BaseTestCase):
    SCENARIO_CFG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'home-automation-scenarios.cfg')

    def setUp(self):
        super(TestScenariosManager, self).setUp()
        self.mgr = ScenariosManager()

    def test01_add_scenario(self):
        scenario_in = Scenario('scenario 1')
        self.mgr.add_scenario('s01', scenario_in)

    def test02_query(self):
        scenarios_count = 10
        for i in range(scenarios_count):
            scenario_in = Scenario('scenario %02d' % i)
            scenario_in.add_action(BasicAction('nop', 'none', '', 'scen%02d.action' % i))
            self.mgr.add_scenario('s%02d' % i, scenario_in)

        scenarios = self.mgr.scenarios
        self.assertEqual(len(scenarios), scenarios_count)
        name, scenario = scenarios[0]
        self.assertEqual(name, 's00')
        self.assertEqual(scenario.label, 'scenario 00')

        scenario_out = self.mgr.get_scenario('s01')
        self.assertIsNotNone(scenario_out)
        action = scenario_out.actions[0]
        self.assertEqual(action.label, "scen01.action")

    def test03_load(self):
        self.mgr.load_scenarios(self.SCENARIO_CFG_FILE_PATH)

        self.assertEqual(len(self.mgr._scenarios), 2)
        scenario = self.mgr.get_scenario("s01")
        self.assertIsNotNone(scenario)
        actions = scenario.actions
        self.assertEqual(len(actions), 2)

    def test04_save(self):
        in_path = self.SCENARIO_CFG_FILE_PATH
        self.mgr.load_scenarios(in_path)

        out_path = "/tmp/scenarios-out.cfg"
        self.mgr.save_scenarios(out_path)

        d_in = json.load(file(in_path, 'rt'))
        d_out = json.load(file(out_path, 'rt'))
        self.assertDictEqual(d_in, d_out)


class MockUpEventManager(Loggable):
    def __init__(self):
        super(MockUpEventManager, self).__init__()
        self.last_event = None
        self.events_count = 0

    def emitEvent(self, var_type, var_name, data):
        self.log_info(
            "emit event var_type=%s var_name=%s data=%s",
            var_type, var_name, data
        )
        self.events_count += 1
        self.last_event = (var_type, var_name, data)


if __name__ == '__main__':
    unittest.main()
