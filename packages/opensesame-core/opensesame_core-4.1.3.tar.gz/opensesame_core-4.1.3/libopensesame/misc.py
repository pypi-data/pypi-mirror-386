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
import os
import re
import os.path
import platform
import sys
import site
from libopensesame import metadata
from libopensesame.oslogging import oslogger


def parse_environment_file():
    r"""Parses the environment.yaml file if it exists."""
    if not os.path.exists(u'environment.yaml'):
        return
    with safe_open(u'environment.yaml') as fd:
        d = safe_yaml_load(fd.read())
    # Convert all values from UTF8 to the filesystem encoding
    for key, val in d.items():
        if isinstance(val, str):
            d[key] = safe_str(safe_decode(val), enc=sys.getfilesystemencoding())
        elif isinstance(val, list):
            d[key] = [
                safe_str(safe_decode(i), enc=sys.getfilesystemencoding())
                for i in val
            ]
        else:
            raise TypeError('values in environment.yaml should be str or list')
    # The Python path is added to sys.path, the rest is added as an environment
    # variable.
    if u'PYTHON_PATH' in d:
        if isinstance(d[u'PYTHON_PATH'], str):
            sys.path = d[u'PYTHON_PATH'].split(';') + sys.path
        else:
            sys.path = d[u'PYTHON_PATH'] + sys.path
        del d[u'PYTHON_PATH']
    for key in (u'OPENSESAME_EXTENSION_PATH', u'OPENSESAME_PLUGIN_PATH'):
        if isinstance(d.get(key, None), list):
            d[key] = u';'.join(d[key])
    os.environ.update(d)


def change_working_dir():
    """A horrifyingly ugly hack to change the working directory under Windows"""
    import libqtopensesame.qtopensesame

    if os.name == "nt":
        try:
            # Extract the part of the description containing the path
            s = str(libqtopensesame.qtopensesame)
            i = s.find(u'from \'') + 6
            j = s.find(u'\'>\'') - 1
            s = s[i:j]
            # Go up the tree until the path of the current script
            while not os.path.exists(os.path.join(s, u'opensesame')) and \
                    not os.path.exists(os.path.join(s, u'opensesame.exe')) and \
                    not os.path.exists(os.path.join(s, u'opensesamerun')) and \
                    not os.path.exists(os.path.join(s, u'opensesamerun.exe')):
                s = os.path.dirname(s)
            os.chdir(s)
            if s not in sys.path:
                sys.path.append(s)
        except Exception as e:
            oslogger.debug(u'failed to change working directory: %s' % e)


def opensesamerun_options():
    """Parse the command line options for opensesamerun"""
    import optparse

    parser = optparse.OptionParser(
        u'usage: opensesamerun [experiment] [options]', version=u'%s \'%s\'' %
        (metadata.__version__, metadata.codename))
    parser.set_defaults(subject=0)
    parser.set_defaults(logfile=None)
    parser.set_defaults(debug=False)
    parser.set_defaults(fullscreen=False)
    parser.set_defaults(width=1024)
    parser.set_defaults(height=768)
    parser.set_defaults(custom_resolution=False)
    group = optparse.OptionGroup(parser, u'Subject and log file options')
    group.add_option(u"-s", u"--subject", action=u"store", dest=u"subject",
                     help=u"Subject number")
    group.add_option(u"-l", u"--logfile", action=u"store", dest=u"logfile",
                     help=u"Logfile")
    parser.add_option_group(group)
    group = optparse.OptionGroup(parser, u"Display options")
    group.add_option(u"-f", u"--fullscreen", action=u"store_true",
                     dest="fullscreen", help=u"Run fullscreen")
    group.add_option(u"-c", u"--custom_resolution", action=u"store_true",
                     dest=u"custom_resolution", help=u"Do not use the display resolution specified in the experiment file")
    group.add_option(u"-w", u"--width", action=u"store",
                     dest=u"width", help=u"Display width")
    group.add_option(u"-e", u"--height", action=u"store", dest=u"height",
                     help=u"Display height")
    parser.add_option_group(group)
    group = optparse.OptionGroup(parser, u"Miscellaneous options")
    group.add_option(u"-d", u"--debug", action=u"store_true", dest=u"debug",
                     help=u"Print lots of debugging messages to the standard output")
    group.add_option(u"--stack", action=u"store_true",
                     dest=u"stack", help=u"Print stack information")
    parser.add_option_group(group)
    parser.add_option_group(group)
    options, args = parser.parse_args(sys.argv)

    # Set the default logfile based on the subject nr
    if options.logfile is None:
        options.logfile = u"subject-%s.csv" % options.subject

    if len(sys.argv) > 1 and os.path.exists:
        options.experiment = sys.argv[1]
    else:
        options.experiment = u""

    try:
        options.subject = int(options.subject)
    except:
        parser.error(u"Subject (-s / --subject) should be numeric")

    try:
        options.width = int(options.width)
    except:
        parser.error(u"Width (-w / --width) should be numeric")

    try:
        options.height = int(options.height)
    except:
        parser.error(u"Height (-e / --height) should be numeric")

    return options


def opensesamerun_ready(options):
    """
    Check if the opensesamerun options are sufficiently complete to run the
    experiment

    Arguments:
    options -- a dictionary containing the options

    Returns:
    True or False, depending on whether the options are sufficient
    """
    # Check if the experiment exists
    if not os.path.exists(options.experiment):
        return False

    # Check if the logfile is writable
    try:
        open(options.logfile, u"w")
    except:
        return False

    # Ready to run!
    return True


def messagebox(title, msg):
    """
    Presents a simple tk messagebox

    Arguments:
    title -- the title of the messagebox
    msg -- the message
    """
    import tkinter as Tkinter
    root = Tkinter.Tk()
    root.title(title)
    l = Tkinter.Label(root, text=msg, justify=Tkinter.LEFT, padx=8, pady=8,
                      wraplength=300)
    l.pack()
    b = Tkinter.Button(root, text=u"Ok", command=root.quit)
    b.pack(side=Tkinter.RIGHT)
    root.mainloop()


def strip_tags(s):
    """
    Strip html tags from a string and convert breaks to newlines.

    Arguments:
    s -- the string to be stripped

    Returns:
    The stripped string
    """
    import re
    return re.compile(r'<.*?>').sub(
        '', str(s).replace("<br />","\n").replace("<br>", "\n"))


def home_folder():
    """
    Determines the home folder.

    Returns:
    A path to the home folder.
    """
    import platform
    if platform.system() == u"Windows":
        home_folder = os.environ[u"APPDATA"]
    elif platform.system() == u"Darwin":
        home_folder = os.environ[u"HOME"]
    elif platform.system() == u"Linux":
        home_folder = os.environ[u"HOME"]
    else:
        home_folder = os.environ[u"HOME"]
    return safe_decode(home_folder, enc=sys.getfilesystemencoding())


def opensesame_folder():
    """
    Determines the folder that contains the OpenSesame executable. This is only
    applicable under Windows.

    Returns:
    The OpenSesame folder or None if the os is not Windows.
    """
    # Determines the directory name of the script or the directory name
    # of the executable
    #
    # There are two scenarios:
    #
    # - OpenSesame is run from source, in which case we go to the OpenSesame
    #   folder by going a levels up from the __file__ folder.
    # - OpenSesame is run in Anaconda, in which case we need to go two levels
    #   up to get out of the site-packages folder.
    if platform.system() == 'Darwin':
        return os.getcwd()
    if platform.system() == 'Windows':
        # To get the opensesame folder, simply jump to levels up
        path = safe_decode(
            os.path.dirname(__file__),
            enc=sys.getfilesystemencoding()
        )
        # The current should not be the site-packages folder, which
        # happens on Anaconda if launched in multiprocess mode.
        path = os.path.normpath(os.path.join(path, '..'))
        if path.endswith('Lib\\site-packages'):
            path = os.path.normpath(os.path.join(path, '..', '..'))
        return path
    return None


def open_url(url):
    """
    Open a URL in an OS specific way. The URL can be a file, website, etc.

    Arguments:
    url -- a url
    """
    oslogger.info(u'opening %s' % url)
    if url.startswith(u'http://') or url.startswith(u'https://'):
        import webbrowser
        webbrowser.open(url)
        return
    import platform
    import subprocess
    if platform.system() == u"Linux":
        pid = subprocess.Popen([u"xdg-open", url]).pid
    elif platform.system() == u"Darwin":
        pid = subprocess.Popen(["open", url]).pid
    elif platform.system() == u"Windows":
        try:
            os.startfile(url)
        except:
            oslogger.error(u"Failed to open '%s'" % url)
    else:
        oslogger.error(u"Failed to open '%s'" % url)


def strip_html(s):
    """
    Strips basic HTML tags from a string.

    Arguments:
    s		--	A string to strip.

    Returns:
    A stripped string.
    """
    s = s.replace(u'<br />', u'\n')
    for tag in [u'<i>', u'</i>', u'<b>', u'</b>']:
        s = s.replace(tag, u'')
    return s


def escape_html(s):
    """
    Escapes a string so that it can be displayed as HTML. This is useful for
    example for tracebacks, which use <> characters.

    Arguments:
    s	--	A string to escape. We assume Unicode input. str objects may cause
                    decoding errors.

    Returns:
    An escaped string.
    """
    # Note that we need to replace the '&' first, otherwise we'll start escaping
    # the escaped characters.
    l = [(u'&', u'&amp;'), (u' ', u'&nbsp;'),
         (u'\t', u'&nbsp;&nbsp;&nbsp;&nbsp;'), (u'<', u'&lt;'),
         (u'>', u'&gt;')]
    for orig, new in l:
        s = s.replace(orig, new)
    return s


snake_case_pattern = re.compile(r'(?<!^)(?=[A-Z])')


def snake_case(s):
    """Turns CamelCase to snake_case"""
    return snake_case_pattern.sub('_', s).lower()
    
    
def camel_case(s):
    """Turns snake_case to CamelCase"""
    return ''.join(x.capitalize() or '_' for x in s.split('_'))


# Build a list of base folders, that is, folders that can have
# opensesame_resources, opensesame_plugins, or opensesame_extensions as
# subfolders. Which folders are available depends on the environment, but the
# following folders are scanned:
#
# - The working directory (cwd)
# - The folder that contains libopensesame (parent_folder)
# - The share folder within an Anaconda/ Miniconda environment
# - The userbase folder:
#		- ~/.local (on Ubuntu 16.04)
# - The user site-packages folder:
#		- ~/.local/lib/python[X]/site-packages (on Ubuntu 16.04)
# - The global site-packages folders (on Ubuntu 16.04):
#		- /usr/local/lib/python3.5/dist-packages
#		- /usr/lib/python3/dist-packages
#		- /usr/lib/python3.5/dist-packages
# - /usr/local/share
# - /usr/share

cwd = os.getcwd()
parent_folder = safe_decode(
    os.path.dirname(os.path.dirname(__file__)),
    enc=sys.getfilesystemencoding()
)
base_folders = [cwd, parent_folder]
# Locate Anaconda/Miniconda share
base_folders.append(os.path.join(
    safe_decode(
        os.path.dirname(os.path.dirname(sys.executable)),
        enc=sys.getfilesystemencoding()
    ),
    u"share"
))
if hasattr(site, u'getuserbase'):
    base_folders.append(os.path.join(
        safe_decode(site.getuserbase(), enc=sys.getfilesystemencoding()),
        u'share'
    ))
if hasattr(site, u'getusersitepackages'):
    base_folders.append(os.path.join(
        safe_decode(site.getusersitepackages(), enc=sys.getfilesystemencoding()),
        u'share'
    ))
if hasattr(site, u'getsitepackages'):
    base_folders += [
        os.path.join(
            safe_decode(folder, enc=sys.getfilesystemencoding()),
            u'share'
        )
        for folder in site.getsitepackages()
    ]
base_folders += [u'/usr/local/share', u'/usr/share']
base_folders = list(filter(os.path.exists, base_folders))
resource_folders = [
    os.path.join(path, u'opensesame_resources')
    for path in base_folders
]
if 'OPENSESAME_RESOURCES_PATH' in os.environ:
    resource_folders.append(os.environ['OPENSESAME_RESOURCES_PATH'])
