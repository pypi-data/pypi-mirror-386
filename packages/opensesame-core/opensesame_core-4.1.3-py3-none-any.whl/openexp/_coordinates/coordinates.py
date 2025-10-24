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
from openexp._canvas.canvas import Canvas
from openexp._mouse.mouse import Mouse


class Coordinates:
    r"""A base class for classes that need to perform coordinate conversions.
    """
    
    def __init__(self):
        r"""Constructor."""
        self._width = self.experiment.var.width
        self._height = self.experiment.var.height
        self._xcenter = self._width/2
        self._ycenter = self._height/2
        self._bottom = self._ycenter
        self._top = -self._ycenter
        self._left = -self._xcenter
        self._right = self._xcenter
        self._mouse_dev = isinstance(self, Mouse)
        self._canvas_dev = isinstance(self, Canvas)
        if not self._mouse_dev and not self._canvas_dev:
            raise TypeError('coordinates class should be coparent with canvas '
                            'or mouse class')

    def none_to_center(self, x, y):
        r"""Interprets None coordinates as the display center.

        Parameters
        ----------
        x : int, float, NoneType
            An X coordinate.
        y : int, float, NoneType
            A Y coordinate.

        Returns
        -------
        tuple
            An (x, y) coordinate tuple.
        """
        if x is None:
            x = 0
        if y is None:
            y = 0
        return x, y

    def to_xy(self, x, y=None):
        r"""Converts coordinates from the OpenSesame reference frame to the
        back-end specific reference frame. `None` values are taken as the
        display center.

        Parameters
        ----------
        x : float, int, NoneType, tuple
            An x coordinate, or an (x,y) tuple.
        y : float, int, NoneType, optional
            A y coordinate. Only applicable if x was not a tuple.

        Returns
        -------
        tuple
            An (x, y) coordinate tuple in the back-end specific reference
            frame.
        """
        raise NotImplementedError()

    def from_xy(self, x, y=None):
        r"""Converts coordinates from the back-end specific reference frame to
        the OpenSesame reference frame.

        Parameters
        ----------
        x : float, int, tuple
            An x coordinate, or an (x,y) tuple.
        y : float, int, NoneType, optional
            A y coordinate. Only applicable if x was not a tuple.

        Returns
        -------
        tuple
            An (x, y) coordinate tuple in the OpenSesame reference frame.
        """
        raise NotImplementedError()


# Non PEP-8 alias for backwards compatibility
coordinates = Coordinates
