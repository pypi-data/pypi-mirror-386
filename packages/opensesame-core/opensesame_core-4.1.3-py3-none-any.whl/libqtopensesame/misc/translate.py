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

Translation logic:

- Context naming:
    - main code: core_[name]
    - items: item_[name]
    - plugins: plugin_[name]
    - extensions: extension_[name]
    - UI files: ui_[name]
- Literals are translated where they are defined
- Wildcards in literals should be part of the translation string
- Translatables should not be broken across lines
- For plugns and extensions, JSON info is extracted,
  and translated when automatic controls are defined
- UI files are extracted, and translated fully automatically
"""
from libopensesame.py3compat import *
from qtpy.QtCore import QCoreApplication


def translation_context(name, category=u'core'):
    r"""A factory that generates a translation method with a fixed context.

    Parameters
    ----------
    name : str
        The name to use for the context.
    name : str, optional
        The category to use for the context.

    Returns
    -------
    FunctionType
        A translation function.
    """
    _context = u'%s_%s' % (category, name)
    return lambda s, context=None: QCoreApplication.translate(_context, s)
