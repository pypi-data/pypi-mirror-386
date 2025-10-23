# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

__all__ = ("ConfigurableActionField",)

from typing import Any, overload

from lsst.pex.config import Config, ConfigField, FieldValidationError
from lsst.pex.config.callStack import getCallStack
from lsst.pex.config.config import _joinNamePath, _typeStr

from . import ActionTypeVar, ConfigurableAction


class ConfigurableActionField(ConfigField[ActionTypeVar]):
    """`ConfigurableActionField` is a subclass of `~lsst.pex.config.Field` that
    allows a single `ConfigurableAction` (or a subclass) to be assigned to it.
    The `ConfigurableAction` is then accessed through this field for further
    configuration.

    Any configuration of this field that is done prior to having a new
    `ConfigurableAction` assigned to it is forgotten.

    Parameters
    ----------
    doc : `str`
        Documentation string.
    dtype : `ConfigurableAction`
        Data type to use for this field.
    default : `lsst.pex.config.Config`, optional
        If default is `None`, the field will default to a default-constructed
        instance of ``dtype``. Additionally, to allow for fewer deep-copies,
        assigning an instance of ``ConfigField`` to ``dtype`` itself is
        considered equivalent to assigning a default-constructed sub-config.
        This means that the argument default can be ``dtype``, as well as an
        instance of ``dtype``.
    check : `~collections.abc.Callable`, optional
        A callback function that validates the field's value, returning `True`
        if the value is valid, and `False` otherwise.
    deprecated : `bool` or `None`, optional
        A description of why this Field is deprecated, including removal date.
        If not `None`, the string is appended to the docstring for this Field.
    """

    # These attributes are dynamically assigned when constructing the base
    # classes
    name: str

    def __set__(
        self,
        instance: Config,
        value: ActionTypeVar | type[ActionTypeVar],
        at: Any = None,
        label: str = "assignment",
    ) -> None:
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")
        name = _joinNamePath(prefix=instance._name, name=self.name)

        if not isinstance(value, self.dtype) and not issubclass(value, self.dtype):
            msg = f"Value {value} is of incorrect type {_typeStr(value)}. Expected {_typeStr(self.dtype)}"
            raise FieldValidationError(self, instance, msg)

        if at is None:
            at = getCallStack()

        if isinstance(value, self.dtype):
            instance._storage[self.name] = type(value)(__name=name, __at=at, __label=label, **value._storage)
        else:
            instance._storage[self.name] = value(__name=name, __at=at, __label=label)
        history = instance._history.setdefault(self.name, [])
        history.append(("config value set", at, label))

    @overload
    def __get__(
        self, instance: None, owner: Any = None, at: Any = None, label: str = "default"
    ) -> ConfigurableActionField[ActionTypeVar]: ...

    @overload
    def __get__(self, instance: Config, owner: Any = None, at: Any = None, label: str = "default") -> Any: ...

    def __get__(self, instance, owner=None, at=None, label="default"):
        result = super().__get__(instance, owner)
        if instance is not None:
            # ignore is due to typing resolved in overloads not translating to
            # type checker not knowing this is not a Field
            result.identity = self.name  # type: ignore
        return result

    def save(self, outfile, instance):
        # docstring inherited from parent
        # This is different that the parent class in that this field must
        # serialize which config class is assigned to this field prior to
        # serializing any assignments to that config class's fields.
        value = self.__get__(instance)
        fullname = _joinNamePath(instance._name, self.name)
        outfile.write(f"{fullname}={_typeStr(value)}\n")
        super().save(outfile, instance)

    def __init__(self, doc, dtype=ConfigurableAction, default=None, check=None, deprecated=None):
        if not issubclass(dtype, ConfigurableAction):
            raise ValueError("dtype must be a subclass of ConfigurableAction")
        super().__init__(doc=doc, dtype=dtype, default=default, check=check, deprecated=deprecated)
