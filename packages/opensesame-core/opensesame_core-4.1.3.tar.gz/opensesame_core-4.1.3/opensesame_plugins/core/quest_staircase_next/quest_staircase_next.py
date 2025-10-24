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
from libopensesame.item import Item
from libopensesame.exceptions import OSException


class QuestNotInitialized(OSException):
    """This exception is raised when a Quest staircase hasn't been initialized.
    """
    pass


class QuestStaircaseNext(Item):

    def reset(self):
        self.var.response_var = 'correct'
        self.var.quest_name = 'default'

    def run(self):
        resp = self.var.get(self.var.response_var)
        try:
            resp = int(resp)
        except (ValueError, TypeError):
            # Don't process non-float responses
            return
        if not hasattr(self.experiment, 'quest') or \
                self.var.quest_name not in self.experiment.quest:
            raise QuestNotInitialized(
                f'quest staircase {self.var.quest_name} has not been initialized with a quest_staircase_init')
        self.experiment.quest[self.var.quest_name].update(
            self.var.quest_test_value, resp)
        self.experiment.quest_set_next_test_value[self.var.quest_name]()
