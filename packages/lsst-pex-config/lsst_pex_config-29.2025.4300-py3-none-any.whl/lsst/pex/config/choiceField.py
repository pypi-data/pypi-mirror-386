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

__all__ = ["ChoiceField"]

from .callStack import getStackFrame
from .config import Field, FieldTypeVar, _typeStr


class ChoiceField(Field[FieldTypeVar]):
    """A configuration field (`~lsst.pex.config.Field` subclass) that allows a
    user to select from a predefined set of values.

    Use ``ChoiceField`` when a configuration can only take one of a predefined
    set of values. Each choice must be of the same type.

    Parameters
    ----------
    doc : `str`
        Documentation string that describes the configuration field.
    dtype : class
        The type of the field's choices. For example, `str` or `int`.
    allowed : `dict`
        The allowed values. Keys are the allowed choices (of ``dtype``-type).
        Values are descriptions (`str`-type) of each choice.
    default : ``dtype``-type, optional
        The default value, which is of type ``dtype`` and one of the allowed
        choices.
    optional : `bool`, optional
        If `True`, this configuration field is *optional*. Default is `True`.
    deprecated : None or `str`, optional
        A description of why this Field is deprecated, including removal date.
        If not None, the string is appended to the docstring for this Field.

    See Also
    --------
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    Field
    ListField
    RangeField
    RegistryField
    """

    def __init__(self, doc, dtype=None, allowed=None, default=None, optional=True, deprecated=None):
        if dtype is None:
            raise ValueError("supplied dtype must not be None")
        if allowed is None:
            raise ValueError("supplied allowed mapping must not be None")
        self.allowed = dict(allowed)
        if optional and None not in self.allowed:
            self.allowed[None] = "Field is optional"

        if len(self.allowed) == 0:
            raise ValueError("ChoiceFields must allow at least one choice")

        Field.__init__(
            self, doc=doc, dtype=dtype, default=default, check=None, optional=optional, deprecated=deprecated
        )

        self.__doc__ += "\n\nAllowed values:\n\n"
        for choice, choiceDoc in self.allowed.items():
            if choice is not None and not isinstance(choice, dtype):
                raise ValueError(
                    f"ChoiceField's allowed choice {choice} is of incorrect type "
                    f"{_typeStr(choice)}. Expected {_typeStr(dtype)}"
                )
            # Force to a string so that additional quotes are added with !r
            self.__doc__ += f"``{str(choice)!r}``\n  {choiceDoc}\n"

        self.source = getStackFrame()

    def _validateValue(self, value):
        Field._validateValue(self, value)
        if value not in self.allowed:
            msg = "Value {} is not allowed.\n\tAllowed values: [{}]".format(
                value, ", ".join(str(key) for key in self.allowed)
            )
            raise ValueError(msg)
