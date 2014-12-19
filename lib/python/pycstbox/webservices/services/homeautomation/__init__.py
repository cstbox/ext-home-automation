#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual - CSTB (eric.pascual@cstb.fr)'

import json

from pycstbox.webservices.wsapp import WSHandler
from pycstbox import log, sysutils, evtmgr
from pycstbox.homeautomation.core import ScenariosManager, Scenario, BasicAction


def _init_(logger=None, settings=None):
    """ Module init function, called by the application framework during the
    services discovery process.

    settings expected content:
     - config_path : automation scenarios configuration file
    """

    if not logger:
        logger = log.getLogger('wsapi.homeautomation')
    _handlers_initparms['logger'] = logger
    _handlers_initparms['settings'] = settings

    logger.info('connecting to Event Manager...')
    evt_mgr = evtmgr.get_object(evtmgr.CONTROL_EVENT_CHANNEL)
    if not evt_mgr:
        raise Exception('cannot get event manager access for channel %s' % evtmgr.CONTROL_EVENT_CHANNEL)
    _handlers_initparms['events_mgr'] = evt_mgr
    logger.info('success')


class BaseHandler(WSHandler):
    """ Root class for requests handlers.

    It takes care of storing shared resources retrieved when initializing the service module.
    """
    _scenarios_mgr = None

    def initialize(self, logger=None, settings=None, **kwargs):
        super(BaseHandler, self).initialize(logger, **kwargs)
        self._scenarios_mgr = ScenariosManager()
        self._scenarios_mgr.load_scenarios(path=settings.get('config_path', None))


class GetAvailableScenarios(BaseHandler):
    """ Returns the list of available automation scenarios.

    The result is a list of pairs (id, label), wrapped in a dictionary keyed by "scenarios" for
    security sake.
    """
    def do_get(self):
        result = [
            {'id': scen_id, 'label': sysutils.to_unicode(scenario.label), 'verb': sysutils.to_unicode(scenario.ui_verb)}
            for scen_id, scenario in self._scenarios_mgr.scenarios
        ]
        self.write({'scenarios': result})


class ScenarioSettings(BaseHandler):
    """ Read and write access to the configuration parameters of an automation scenario.
    """
    def do_get(self, scen_id):
        try:
            scenario = self._scenarios_mgr.get_scenario(scen_id)
            self.write(scenario.as_dict())
        except KeyError:
            self.set_status(404)
            self.write({
                'message': 'scenario not found : %s' % scen_id
            })

    def do_put(self, scen_id):
        try:
            scenario = self._scenarios_mgr.get_scenario(scen_id)
        except KeyError:
            self.set_status(404)
            self.write({
                'message': 'scenario not found : %s' % scen_id
            })
        else:
            try:
                new_settings = json.loads(self.request.body)
            except ValueError:
                self.set_status(400)
                self.write({
                    'message': 'invalid JSON data passed in request body'
                })
            else:
                scenario.update(new_settings)
                self._scenarios_mgr.save_scenarios()

    # def put(self, scen_id):
    #     if scen_id in self._scenarios_mgr:
    #         self.set_status(400)
    #         self.write({
    #             'message': 'duplicate scenario name (%s)' % scen_id
    #         })
    #
    #     else:
    #         new_settings = json.loads(self.request.body)
    #         scenario = Scenario(
    #             label=new_settings[Scenario.KEY_LABEL],
    #             actions=[BasicAction.from_dict(d) for d in new_settings[Scenario.KEY_ACTIONS]],
    #             ui_verb=new_settings[Scenario.KEY_UI_VERB]
    #         )
    #         self._scenarios_mgr.add_scenario(scen_id, scenario)
    #         self._scenarios_mgr.save_scenarios()

    def delete(self, scen_id):
        try:
            self._scenarios_mgr.remove_scenario(scen_id)
        except KeyError:
            self.set_status(404)
            self.write({
                'message': 'scenario not found : %s' % scen_id
            })
        else:
            self._scenarios_mgr.save_scenarios()


class ScenarioExecution(BaseHandler):
    """ Triggers the execution of an automation scenario.
    """
    _evtmgr = None

    def initialize(self, **kwargs):
        super(ScenarioExecution, self).initialize(**kwargs)
        self._evtmgr = kwargs['events_mgr']
        if not self._evtmgr:
            raise ValueError('no event manager provided')

    def do_post(self, scen_id):
        self.do_get(scen_id)

    def do_get(self, scen_id):
        try:
            scenario = self._scenarios_mgr.get_scenario(scen_id)
        except KeyError:
            self.set_status(404)
            self.write({
                'message': 'scenario not found : %s' % scen_id
            })
        else:
            scenario.execute(self._evtmgr)


_handlers_initparms = {}

handlers = [
    (r"/scenarios", GetAvailableScenarios, _handlers_initparms),
    (r"/scenario/(?P<scen_id>[^/]+)/settings", ScenarioSettings, _handlers_initparms),
    (r"/scenario/(?P<scen_id>[^/]+)/execute", ScenarioExecution, _handlers_initparms),
]
