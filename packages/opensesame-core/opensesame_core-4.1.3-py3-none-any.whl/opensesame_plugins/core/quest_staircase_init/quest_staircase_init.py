# -*- coding:utf-8 -*-

"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""
from libopensesame.py3compat import *
from libopensesame.exceptions import InvalidValue
from libopensesame.oslogging import oslogger
from libopensesame.item import Item
try:
    import Quest
except ImportError:
    oslogger.debug('Failed to import Quest, trying psychopy.contrib.quest')
    from psychopy.contrib import quest as Quest


class QuestStaircaseInit(Item):

    def reset(self):
        self.var.t_guess = .5
        self.var.t_guess_sd = .25
        self.var.p_threshold = .75
        self.var.beta = 3.5
        self.var.delta = .01
        self.var.gamma = .5
        self.var.quest_name = 'default'
        self.var.test_value_method = 'quantile'
        self.var.min_test_value = 0
        self.var.max_test_value = 1
        self.var.var_test_value = 'quest_test_value'

    def quest_set_next_test_value(self):
        quest = self.experiment.quest[self.var.quest_name]
        if self.var.test_value_method == 'quantile':
            fnc = quest.quantile
        elif self.var.test_value_method == 'mean':
            fnc = quest.mean
        elif self.var.test_value_method == 'mode':
            fnc = quest.mode
        else:
            raise InvalidValue(
                f'Unknown test_value_method {self.var.test_value_method}')
        test_value = max(self.var.min_test_value,
                         min(self.var.max_test_value, fnc()))
        oslogger.debug(f'quest_test_value = {test_value}')
        self.experiment.var.quest_test_value = test_value
        self.experiment.var.set(self.var.var_test_value, test_value)

    def prepare(self):
        if not hasattr(self.experiment, 'quest'):
            self.experiment.quest = {}
            self.experiment.quest_set_next_test_value = {}
        self.experiment.quest[self.var.quest_name] = Quest.QuestObject(
            self.var.t_guess, self.var.t_guess_sd, self.var.p_threshold,
            self.var.beta, self.var.delta, self.var.gamma)
        self.experiment.quest_set_next_test_value[self.var.quest_name] = \
            self.quest_set_next_test_value
        self.quest_set_next_test_value()

    def var_info(self):
        """Gives a list of dictionaries with variable descriptions.

        Returns
        -------
        list
            A list of (name, description) tuples.
        """
        return super().var_info() + [('quest_test_value',
                                      '(Determined by Quest procedure)')]
