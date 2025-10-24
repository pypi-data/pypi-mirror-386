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
from libopensesame.oslogging import oslogger
from libopensesame.exceptions import OSException, UnexpectedError
import platform
import sys
import os
import signal
import multiprocessing


class OutputChannel:
    """Passes messages from child process back to main process.
    
    Parameters
    ----------
    channel:
        A multiprocessing.JoinableQueue object that is referenced from the
        main process.
    orig:
        The original stdout or stderr to also print the messages to.
    """
    def __init__(self, channel, orig=None):
        self.channel = channel
        self.orig = orig

    def write(self, m):
        """Writes a message to the queue.

        Parameters
        ----------
        m:
            The message to write. Should be a string or an (Exception,
            traceback) tuple.
        """
        self.channel.put(m)

    def flush(self):
        """Dummy function to mimic the stderr.flush() function."""
        if self.orig:
            self.orig.flush()
        else:
            pass

    def isatty(self):
        """Indicates that the output is not attached to a terminal."""
        return False


class ExperimentProcess(multiprocessing.Process):
    """Creates a new process to run an experiment in.

    Parameters
    ----------
    exp:
        An instance of libopensesame.experiment.experiment
    output:
        A reference to the queue object created in and used to communicate with
        the main process.
    """
    def __init__(self, exp, output):
        multiprocessing.Process.__init__(self)
        self.output = output
        # The experiment object is troublesome to serialize,
        # therefore pull out all relevant data to pass on to the new process
        # and rebuild the exp object in there.
        self.script = exp.to_string()
        self.pool_folder = exp.pool.folder()
        self.subject_nr = exp.var.subject_nr
        self.experiment_path = exp.experiment_path
        self.fullscreen = exp.var.fullscreen == u'yes'
        self.logfile = exp.logfile
        self.killed = False

    def run(self):
        """
        Everything in this function is run in a new process, therefore all
        import statements are put in here. The function reroutes all output to
        stdin and stderr to the pipe to the main process so OpenSesame can
        handle all prints and errors.
        """
        import os
        import sys
        from libopensesame import misc
        from libopensesame.experiment import experiment
        # Under Windows, change the working directory to the OpenSesame folder,
        # so that the new process can find the main script.
        if os.name == u'nt':
            os.chdir(misc.opensesame_folder())
            os.environ['PATH'] += ';' + os.getcwd()
        # Reroute output to OpenSesame main process, so everything will be
        # printed in the Debug window there.
        pipeToMainProcess = OutputChannel(self.output)
        sys.stderr = sys.stdout = pipeToMainProcess
        oslogger.start(u'runtime')
        # First initialize the experiment and catch any resulting Exceptions
        try:
            exp = experiment(
                string=self.script, pool_folder=self.pool_folder,
                experiment_path=self.experiment_path,
                fullscreen=self.fullscreen, subject_nr=self.subject_nr,
                logfile=self.logfile)
        except Exception as e:
            if not isinstance(e, OSException):
                e = UnexpectedError('An unexpected error occurred while '
                                    'building the experiment')
            # Communicate the exception and exit with error
            self.output.put(e)
            sys.exit(1)
        oslogger.info(u'Starting experiment as %s' % self.name)
        # Run the experiment and catch any Exceptions.
        e_run = None
        exp.set_output_channel(self.output)
        try:
            exp.run()
            oslogger.info('experiment finished!')
        except Exception as e:
            if not isinstance(e, OSException):
                e = UnexpectedError('An unexpected error occurred while '
                                    'running the experiment')
            e_run = e
        # Communicate the exception. We do this before calling exp.end()
        # because Python may crash in this step and we need to send the
        # exception before that happens.
        if e_run is not None:
            self.output.put(e_run)
        # End the experiment and catch any Exceptions. These exceptions are just
        # printed out and not explicitly passed on to the user, because they are
        # less important than the run-related exceptions.
        try:
            exp.end()
        except Exception as e_exp:
            oslogger.error(
                u'An Exception occurred during exp.end(): %s' % e_exp)
        exp.transmit_workspace()
        # Exit with error status if an exception occurred.
        if e_run is not None:
            sys.exit(1)
        # Exit with success
        sys.exit(0)

    def kill(self):

        oslogger.info(u'killing experiment process')
        try:
            os.kill(
                self.pid,
                signal.SIGKILL if hasattr(
                    signal, u'SIGKILL') else signal.SIGTERM
            )
        except OSError:
            oslogger.warning(u'failed to kill experiment process')
        self.killed = True
