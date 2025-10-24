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
from libopensesame.exceptions import InvalidValue, MissingDependency
from openexp.sampler import Sampler
try:
    import numpy as np
    from scipy import signal
except ImportError:
    np = None
    signal = None


def Synth(experiment, osc="sine", freq=440, length=100, attack=0, decay=5,
          **playback_args):
    """A factory that synthesizes a sound and returns it as a `Sampler
    object`. For a full description of keywords, see
    `python_workspace_api.Synth`.

    For backwards compatibility, this function behaves as though it is a
    back-end.

    Parameters
    ----------
    experiment : Experiment
        The experiment object.

    Returns
    -------
    sampler
        A Sampler object.
    """
    if np is None:
        raise MissingDependency(
            'The synth is not available, because numpy is missing.')
    if attack < 0 or attack > length:
        raise InvalidValue(
            'Attack must be a numeric value between 0 and the sound length')
    if decay < 0 or decay > length:
        raise InvalidValue(
            'Decay must be a numeric value between 0 and the sound length')
    # We need to multiply the rate by two to get a stereo signal
    rate = 2*experiment.var.get('sound_freq', 48000)
    signal = osc_gen(osc, key_to_freq(freq), length, rate)
    _envelope = envelope(length, attack, decay, rate)
    sound = to_int_16(signal * _envelope)
    return Sampler(experiment, sound, **playback_args)


def key_to_freq(key):
    r"""Converts a key (e.g., A1) to a frequency.

    Parameters
    ----------
    key : str, unicode, int, float
        A string like "A1", "eb2", etc, or a numeric frequency (in which case
        the frequency is simply returned as a float).

    Returns
    -------
    float
        A frequency in hertz.

    Examples
    --------
    >>> from openexp.synth import synth
    >>> my_synth = synth(exp)
    >>> print('An a2 is %d Hz' % my_synth.key_to_freq('a2'))
    """
    if type(key) in [int, float]:
        return key
    if not isinstance(key, str) or len(key) < 2:
        raise InvalidValue(
            f"{key} is not a valid note, expecting something like 'A1'")
    n = key[:-1].lower()
    try:
        o = int(key[-1])
    except:
        raise InvalidValue(
            f"{key} is not a valid note, expecting something like 'A1'")
    if n == "a":
        f = 440.0
    elif n == "a#" or n == "bb":
        f = 466.16
    elif n == "b":
        f = 493.92
    elif n == "c":
        f = 523.28
    elif n == "c#" or n == "db":
        f = 554.40
    elif n == "d":
        f = 587.36
    elif n == "d#" or n == "eb":
        f = 698.47
    elif n == "e":
        f = 659.48
    elif n == "f":
        f = 698.48
    elif n == "f#" or n == "gb":
        f = 740.00
    elif n == "g":
        f = 784.00
    elif n == "ab" or n == "g#":
        f = 830.64
    else:
        raise InvalidValue(
            f"{key} is not a valid note, expecting something like 'A1'")
    if o < 1:
        o = 0.5 ** (abs(o) + 1)
        freq = f * o
    else:
        freq = f * o
    return freq


def osc_gen(_type, freq, length, rate):

    length *= .001
    t = np.linspace(0, length, int(length*rate))
    if _type == 'square':
        return signal.square(2 * np.pi * freq * t)
    if _type == 'saw':
        return signal.sawtooth(2 * np.pi * freq * t)
    if _type == 'sine':
        return np.sin(2 * np.pi * freq * t)
    if _type == 'white_noise':
        return np.random.random(int(length * rate)) * 2 - 1
    raise InvalidValue('Invalid oscillator: %s' % _type)


def envelope(length, attack, decay, rate):
    r"""An envelope generator that determines the volume profile of the sound."""
    length *= .001
    attack *= .001
    decay *= .001
    e = np.ones(int(length*rate))
    if attack > 0:
        attack = int(attack*rate)
        e[:attack] *= np.linspace(0, 1, attack)
    if decay > 0:
        decay = int(decay*rate)
        e[-decay:] *= np.linspace(1, 0, decay)
    return e


def to_int_16(a):
    r"""Converts the float array to an 16 bit int array, which is a more
    typical sound format.
    """
    a *= 32767
    return a.astype(np.int16)


# Non PEP-8 alias for backwards compatibility
synth = Synth
