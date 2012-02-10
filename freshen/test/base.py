#-*- coding: utf8 -*-

import traceback
import sys
import re

from freshen.context import ftc, scc
from freshen.stepregistry import UndefinedStepImpl


class ExceptionWrapper(Exception):

    def __init__(self, e, step, discard_frames=0):
        e = list(e)
        while discard_frames:
            e[2] = e[2].tb_next
            discard_frames -= 1
        self.e = e
        self.step = step

    def __str__(self):
        return "".join(traceback.format_exception(*self.e))


class FeatureSuite(object):

    def setUp(self):
        #log.debug("Clearing feature context")
        ftc.clear()


class FreshenTestCase(object):

    start_live_server = True
    database_single_transaction = True
    database_flush = True
    selenium_start = False
    no_database_interaction = False
    make_translations = True
    required_sane_plugins = ["django", "http"]
    django_plugin_started = False
    http_plugin_started = False
    last_step = None
    re_scenario_outline_values = re.compile('<([^>]+)>')

    test_type = "http"

    def __init__(self, step_runner, step_registry, feature, scenario, feature_suite):
        self.feature = feature
        self.scenario = scenario
        self.context = feature_suite
        self.step_registry = step_registry
        self.step_runner = step_runner
        self._description = None
        self.show_all_scenario_params = False

    @property
    def description(self):
        if not self._description:
            desc = self.feature.name + ": " + self.scenario.name
            params = self.scenario.params
            if not params: return desc
            keys = self.re_scenario_outline_values.findall(desc)
            d_params = dict(params)
            for k in keys:
                val = d_params.get(k)
                if val is not None:
                    desc = desc.replace('<%s>' % k, val)
            if self.show_all_scenario_params:
                resulting_params = ['%s=%s' % (p[0], p[1]) for p in params if p[0] not in keys]
                if resulting_params:
				    desc = '%s (%s)' % (desc, ','.join(resulting_params))
            self._description = desc
        return self._description

    def id(self): return str(self.feature.__class__)

    def setUp(self):
        #log.debug("Clearing scenario context")
        scc.clear()

    def runAfterStepHooks(self):
        for hook_impl in reversed(self.step_registry.get_hooks('after_step', self.scenario.get_tags())):
            hook_impl.run(self.scenario)

    def runStep(self, step, discard_frames=0):
        try:
            self.last_step = step
            return self.step_runner.run_step(step)
        except (AssertionError, UndefinedStepImpl, ExceptionWrapper):
            raise
        except:
            raise ExceptionWrapper(sys.exc_info(), step, discard_frames)
        self.runAfterStepHooks()

    def runScenario(self):
        raise NotImplementedError('Must be implemented by subclasses')
