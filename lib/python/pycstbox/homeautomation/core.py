#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of CSTBox.
#
# CSTBox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CSTBox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with CSTBox.  If not, see <http://www.gnu.org/licenses/>.

""" Home automation package core definitions.
"""

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import json
import os.path

from collections import namedtuple

from pycstbox.evtmgr import EventManagerObject
from pycstbox.log import Loggable


class Scenario(Loggable):
    """ A scenario is a sequence of basic actions.

    A scenario can be executed.
    """
    KEY_LABEL = 'label'
    KEY_ACTIONS = 'actions'

    def __init__(self, label, actions=None):
        """
        :param str label: a human readable label
        :param actions: the list of actions of the scenario
        :type actions: list of [BasicAction]
        """
        self._label = label
        self._actions = actions[:] if actions else []
        super(Scenario, self).__init__()

    @property
    def label(self):
        return self._label

    @property
    def actions(self):
        """ Returns the sequence of actions
        :rtype: list of [BasicAction]
        """
        return self._actions

    def add_action(self, action):
        """ Appends an action to the sequence.
        :param BasicAction action: the action to be added
        """
        if not action:
            raise ValueError('parameter is mandatory')
        if not isinstance(action, BasicAction):
            raise TypeError('action parameter type mismatch')
        self._actions.append(action)

    def update(self, actions):
        """ Replaces the action sequence by a copy of the provided one.
        :param actions: the new list of actions
        :type actions: list of [BasicAction]
        """
        if not actions:
            raise ValueError("parameter 'actions' is mandatory")
        self._actions = actions[:]

    def clear(self):
        """ Empties the action list
        """
        self._actions.clear()

    def execute(self, event_manager):
        """ Executes the actions of the scenario in the order they have
        been recorded.

        :param EventManagerObject event_manager: the event manager to be used by actions
        """
        if not event_manager:
            raise ValueError("parameter 'event_manager' is mandatory")

        for action in self._actions:
            self.log_info("executing %s", action)
            action.execute(event_manager)

    def as_dict(self):
        return {
            self.KEY_LABEL: self._label,
            self.KEY_ACTIONS: [a._asdict() for a in self._actions]
        }

    def update(self, d):
        """ Updates the scenario definition from provided settings.
        :param dict d: new settings
        """
        new_s = self.from_dict(d)
        self._label = new_s._label
        self._actions = new_s._actions

    @classmethod
    def from_dict(cls, d):
        label = d['label']
        actions_cfg = d['actions']
        actions = [
            BasicAction(
                action['verb'],
                action['target'],
                action.get('data', None),
                action.get('label', None)
            ) for action in actions_cfg
        ]
        return Scenario(label=label, actions=actions)


class BasicAction(namedtuple('BasicAction', 'verb target data label')):
    """ An action to control an equipment, such as a switch, a dimmer,
     an HVAC device,...

     Actions are executed by emitting the associated control event, using
     the verb and target set at creation time
    """
    def __new__(cls, verb, target, data=None, label=None):
        """
        :param str verb: the type of the event emitted to realize the action
        :param str target: identification of the target device
        :param data: the data for the action if any
        :param str label: an optional human friendly label attached to the action
        """
        if not verb or not target:
            raise ValueError("parameters 'verb' and 'target' are mandatory")
        if not label:
            label = verb + ' ' + target + ' ' + cls._interpret_param(verb, data)
        return super(BasicAction, cls).__new__(cls, verb, target, data, label)

    @classmethod
    def from_dict(cls, d):
        return cls(d['verb'], d['target'], d.get('data', None), d.get('label', None))

    @staticmethod
    def _interpret_param(verb, parameter):
        if verb == 'switch':
            return 'on' if parameter else 'off'
        elif verb == 'dim':
            return "%d%%" % int(parameter)
        else:
            return parameter

    def execute(self, event_manager):
        """ Execute the action by sending the associated event, based on its
        verb and target.

        :param EventManagerObject event_manager: the event manager used for sending
        the action event
        """
        event_manager.emitEvent(self.verb, self.target, str(self.data))

    def __str__(self):
        return("%s(%s, %s, %s)" %
               (self.__class__.__name__, self.verb, self.target, self.data)
        )


class ScenariosManager(Loggable):
    """ Manages all known scenarios and their persistence in storage.

    It is organized on a directory keeping track of the definitions of available scenarios.
    """
    DEFAULT_STORAGE_PATH = "/etc/cstbox/home-automation-scenarios.cfg"

    def __init__(self):
        super(ScenariosManager, self).__init__()

        self._scenarios = {}

    @property
    def scenarios(self):
        """ Returns the list of available scenarios, as pairs composed of the scenario id
        and the scenario definition.

        The list is sorted by scenario names.

        :return: the list of scenarios
        :rtype: list of [Scenario]
        """
        return sorted(self._scenarios.items())

    def __contains__(self, name):
        return name in self._scenarios

    def get_scenario(self, id_):
        """ Returns a scenario given its id.
        :param str id_: the id of the requested scenario
        :return: the scenario
        :rtype: Scenario
        :raise: KeyError if not found
        """
        return self._scenarios[id_]

    def add_scenario(self, id_, scenario):
        """ Adds a scenario to the directory
        :param str id_: the id under which the scenario is registered
        :param Scenario scenario: the scenario definition
        """
        if not id_ or not scenario:
            raise ValueError("parameter 'id_' and 'scenario' are mandatory")
        if not isinstance(scenario, Scenario):
            raise TypeError("parameter 'scenario' type mismatch")

        self._scenarios[id_] = scenario

    def remove_scenario(self, id_):
        """ Removes a scenario from the directory
        :param str id_: the id of the scenario to be removed
        :raise: KeyError if not found
        """
        if not id_:
            raise ValueError("parameter 'id_' is mandatory")
        del self._scenarios[id_]

    def load_scenarios(self, path=None):
        """ Loads the scenario definitions from a given file.

        Definitions are stored as a JSON file, with the following structure :
        {
            <scenario_name> : {
                "label" : "...",
                "actions" : [
                    {"label": "...", "label": "...", "verb": "....", "target": "...", "data": "..."},
                    ...
                ]
            }
        }
        :param str path: the data file path (default: DEFAULT_STORAGE_PATH)
        :raise: ValueError if file not found
        :raise: json.JSONError if file content is not valid
        """
        if not path:
            path = self.DEFAULT_STORAGE_PATH

        if not os.path.isfile(path):
            raise ValueError("path '%s' not found or is not a file" % path)

        self.log_info('loading scenario definitions from %s', path)
        self._scenarios = {}
        for k, v in json.load(file(path, "rt")).iteritems():
            self._scenarios[k] = Scenario.from_dict(v)

    def save_scenarios(self, path=None):
        """ Stores the scenario definitions in the indicated file.

        :param str path: target file path (default: DEFAULT_STORAGE_PATH)
        """
        if not path:
            path = self.DEFAULT_STORAGE_PATH

        self.log_info('storing scenario definitions to %s', path)
        out = {
            k: v.as_dict()
            for k, v in self._scenarios.iteritems()
        }
        json.dump(out, file(path, 'wt'), indent=4)