# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__all__ = ("Color", "format")

import os
import re
import sys


class Color:
    """A controller that determines whether strings should be colored.

    Parameters
    ----------
    text : `str`
        Text content to print to a terminal.
    category : `str`
        Semantic category of the ``text``. See `categories` for possible
        values.

    Raises
    ------
    RuntimeError
        Raised when the ``category`` is not a key of ``Color.categories``.

    Notes
    -----
    The usual usage is ``Color(string, category)`` which returns a string that
    may be printed; categories are given by the keys of `Color.categories`.

    `Color.colorize` may be used to set or retrieve whether the user wants
    color. It always returns `False` when `sys.stdout` is not attached to a
    terminal.
    """

    categories = {
        "NAME": "blue",
        "VALUE": "yellow",
        "FILE": "green",
        "TEXT": "red",
        "FUNCTION_NAME": "blue",
    }
    """Mapping of semantic labels to color names (`dict`).

    Notes
    -----
    The default categories are:

    - ``'NAME'``
    - ``'VALUE'``
    - ``'FILE'``
    - ``'TEXT'``
    - ``'FUNCTION_NAME'``
    """

    colors = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
    }
    """Mapping of color names to terminal color codes (`dict`).
    """

    _colorize = True

    def __init__(self, text, category):
        try:
            color = Color.categories[category]
        except KeyError as e:
            raise RuntimeError(f"Unknown category: {category}") from e

        self.rawText = str(text)
        x = color.lower().split(";")
        self.color, bold = x.pop(0), False
        if x:
            props = x.pop(0)
            if props in ("bold",):
                bold = True

        try:
            self._code = "%s" % (30 + Color.colors[self.color])
        except KeyError as e:
            raise RuntimeError(f"Unknown colour: {self.color}") from e

        if bold:
            self._code += ";1"

    @staticmethod
    def colorize(val=None):
        """Get or set whether the string should be colorized.

        Parameters
        ----------
        val : `bool` or `dict`, optional
            The value is usually a bool, but it may be a dict which is used
            to modify `Color.categories`.

        Returns
        -------
        shouldColorize : `bool`
            If `True`, the string should be colorized. A string **will not** be
            colorized if standard output or standard error are not attached to
            a terminal or if the ``val`` argument was `False`.

            Only strings written to a terminal are colorized.
        """
        if val is not None:
            Color._colorize = val

            if isinstance(val, dict):
                unknown = []
                for k in val:
                    if k in Color.categories:
                        if val[k] in Color.colors:
                            Color.categories[k] = val[k]
                        else:
                            print(f"Unknown colour {val[k]} for category {k}", file=sys.stderr)
                    else:
                        unknown.append(k)

                if unknown:
                    print("Unknown colourizing category: {}".format(" ".join(unknown)), file=sys.stderr)

        return Color._colorize if sys.stdout.isatty() else False

    def __str__(self):
        if not self.colorize():
            return self.rawText

        base = "\033["

        prefix = base + self._code + "m"
        suffix = base + "m"

        return prefix + self.rawText + suffix


def _colorize(text, category):
    text = Color(text, category)
    return str(text)


def format(config, name=None, writeSourceLine=True, prefix="", verbose=False):
    """Format the history record for a configuration, or a specific
    configuration field.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        A configuration instance.
    name : `str`, optional
        The name of a configuration field to specifically format the history
        for. Otherwise the history of all configuration fields is printed.
    writeSourceLine : `bool`, optional
        If `True`, prefix each printout line with the code filename and line
        number where the configuration event occurred. Default is `True`.
    prefix : `str`, optional
        A prefix for to add to each printout line. This prefix occurs first,
        even before any source line. The default is an empty string.
    verbose : `bool`, optional
        Default is `False`.
    """
    if name is None:
        for i, name in enumerate(config.history.keys()):
            if i > 0:
                print()
            print(format(config, name))

    outputs = []
    for value, stack, _ in config.history.get(name, []):
        output = []
        for frame in stack:
            if frame.function in (
                "__new__",
                "__set__",
                "__setattr__",
                "execfile",
                "wrapper",
            ) or os.path.split(frame.filename)[1] in ("argparse.py", "argumentParser.py"):
                if not verbose:
                    continue

            line = []
            if writeSourceLine:
                line.append(
                    [
                        f"{frame.filename}:{frame.lineno}",
                        "FILE",
                    ]
                )

            line.append(
                [
                    frame.content,
                    "TEXT",
                ]
            )
            if False:
                line.append(
                    [
                        frame.function,
                        "FUNCTION_NAME",
                    ]
                )

            output.append(line)

        outputs.append([value, output])

    if outputs:
        # Find the maximum widths of the value and file:lineNo fields.
        if writeSourceLine:
            sourceLengths = []
            for _, output in outputs:
                sourceLengths.append(max([len(x[0][0]) for x in output]))
            sourceLength = max(sourceLengths)

        valueLength = len(prefix) + max([len(str(value)) for value, _ in outputs])

    # Generate the config history content.
    msg = []
    fullname = f"{config._name}.{name}" if config._name is not None else name
    msg.append(_colorize(re.sub(r"^root\.", "", fullname), "NAME"))
    for value, output in outputs:
        if value is not None:
            line = prefix + _colorize(f"{value:<{valueLength}}", "VALUE") + " "
        else:
            line = prefix + _colorize("None", "VALUE") + " "
        for i, vt in enumerate(output):
            if writeSourceLine:
                vt[0][0] = f"{vt[0][0]:<{sourceLength}}"

            output[i] = " ".join([_colorize(v, t) for v, t in vt])

        line += f"\n{'':>{valueLength + 1}}".join(output)
        msg.append(line)

    return "\n".join(msg)
