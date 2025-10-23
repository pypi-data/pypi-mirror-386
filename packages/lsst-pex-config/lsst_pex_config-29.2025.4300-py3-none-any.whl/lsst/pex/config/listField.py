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

__all__ = ["ListField"]

import collections.abc
import weakref
from collections.abc import Iterable, MutableSequence
from typing import Any, Generic, overload

from .callStack import getCallStack, getStackFrame
from .comparison import compareScalars, getComparisonName
from .config import (
    Config,
    Field,
    FieldTypeVar,
    FieldValidationError,
    UnexpectedProxyUsageError,
    _autocast,
    _joinNamePath,
    _typeStr,
)


class List(collections.abc.MutableSequence[FieldTypeVar]):
    """List collection used internally by `ListField`.

    Parameters
    ----------
    config : `lsst.pex.config.Config`
        Config instance that contains the ``field``.
    field : `ListField`
        Instance of the `ListField` using this ``List``.
    value : sequence
        Sequence of values that are inserted into this ``List``.
    at : `list` of `~lsst.pex.config.callStack.StackFrame`
        The call stack (created by `lsst.pex.config.callStack.getCallStack`).
    label : `str`
        Event label for the history.
    setHistory : `bool`, optional
        Enable setting the field's history, using the value of the ``at``
        parameter. Default is `True`.

    Raises
    ------
    FieldValidationError
        Raised if an item in the ``value`` parameter does not have the
        appropriate type for this field or does not pass the
        `ListField.itemCheck` method of the ``field`` parameter.
    """

    def __init__(self, config, field, value, at, label, setHistory=True):
        self._field = field
        self._config_ = weakref.ref(config)
        self._history = self._config._history.setdefault(self._field.name, [])
        self._list = []
        self.__doc__ = field.doc
        if value is not None:
            try:
                for i, x in enumerate(value):
                    self.insert(i, x, setHistory=False)
            except TypeError as e:
                msg = f"Value {value} is of incorrect type {_typeStr(value)}. Sequence type expected"
                raise FieldValidationError(self._field, config, msg) from e
        if setHistory:
            self.history.append((list(self._list), at, label))

    @property
    def _config(self) -> Config:
        # Config Fields should never outlive their config class instance
        # assert that as such here
        value = self._config_()
        assert value is not None
        return value

    def validateItem(self, i, x):
        """Validate an item to determine if it can be included in the list.

        Parameters
        ----------
        i : `int`
            Index of the item in the `list`.
        x : object
            Item in the `list`.

        Raises
        ------
        FieldValidationError
            Raised if an item in the ``value`` parameter does not have the
            appropriate type for this field or does not pass the field's
            `ListField.itemCheck` method.
        """
        if not isinstance(x, self._field.itemtype) and x is not None:
            msg = (
                f"Item at position {i} with value {x} is of incorrect type {_typeStr(x)}. "
                f"Expected {_typeStr(self._field.itemtype)}"
            )
            raise FieldValidationError(self._field, self._config, msg)

        if self._field.itemCheck is not None and not self._field.itemCheck(x):
            msg = f"Item at position {i} is not a valid value: {x}"
            raise FieldValidationError(self._field, self._config, msg)

    def list(self):
        """Sequence of items contained by the `List` (`list`)."""
        return self._list

    history = property(lambda x: x._history)
    """Read-only history.
    """

    def __contains__(self, x):
        return x in self._list

    def __len__(self):
        return len(self._list)

    @overload
    def __setitem__(
        self, i: int, x: FieldTypeVar, at: Any = None, label: str = "setitem", setHistory: bool = True
    ) -> None: ...

    @overload
    def __setitem__(
        self,
        i: slice,
        x: Iterable[FieldTypeVar],
        at: Any = None,
        label: str = "setitem",
        setHistory: bool = True,
    ) -> None: ...

    def __setitem__(self, i, x, at=None, label="setitem", setHistory=True):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")
        if isinstance(i, slice):
            k, stop, step = i.indices(len(self))
            for j, xj in enumerate(x):
                xj = _autocast(xj, self._field.itemtype)
                self.validateItem(k, xj)
                x[j] = xj
                k += step
        else:
            x = _autocast(x, self._field.itemtype)
            self.validateItem(i, x)

        self._list[i] = x
        if setHistory:
            if at is None:
                at = getCallStack()
            self.history.append((list(self._list), at, label))

    @overload
    def __getitem__(self, i: int) -> FieldTypeVar: ...

    @overload
    def __getitem__(self, i: slice) -> MutableSequence[FieldTypeVar]: ...

    def __getitem__(self, i):
        return self._list[i]

    def __delitem__(self, i, at=None, label="delitem", setHistory=True):
        if self._config._frozen:
            raise FieldValidationError(self._field, self._config, "Cannot modify a frozen Config")
        del self._list[i]
        if setHistory:
            if at is None:
                at = getCallStack()
            self.history.append((list(self._list), at, label))

    def __iter__(self):
        return iter(self._list)

    def insert(self, i, x, at=None, label="insert", setHistory=True):
        """Insert an item into the list at the given index.

        Parameters
        ----------
        i : `int`
            Index where the item is inserted.
        x : object
            Item that is inserted.
        at : `list` of `~lsst.pex.config.callStack.StackFrame` or `None`,\
                optional
            The call stack (created by
            `lsst.pex.config.callStack.getCallStack`).
        label : `str`, optional
            Event label for the history.
        setHistory : `bool`, optional
            Enable setting the field's history, using the value of the ``at``
            parameter. Default is `True`.
        """
        if at is None:
            at = getCallStack()
        self.__setitem__(slice(i, i), [x], at=at, label=label, setHistory=setHistory)

    def __repr__(self):
        return repr(self._list)

    def __str__(self):
        return str(self._list)

    def __eq__(self, other):
        if other is None:
            return False
        try:
            if len(self) != len(other):
                return False

            for i, j in zip(self, other, strict=True):
                if i != j:
                    return False
            return True
        except AttributeError:
            # other is not a sequence type
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __setattr__(self, attr, value, at=None, label="assignment"):
        if hasattr(getattr(self.__class__, attr, None), "__set__"):
            # This allows properties to work.
            object.__setattr__(self, attr, value)
        elif attr in self.__dict__ or attr in ["_field", "_config_", "_history", "_list", "__doc__"]:
            # This allows specific private attributes to work.
            object.__setattr__(self, attr, value)
        else:
            # We throw everything else.
            msg = f"{_typeStr(self._field)} has no attribute {attr}"
            raise FieldValidationError(self._field, self._config, msg)

    def __reduce__(self):
        raise UnexpectedProxyUsageError(
            f"Proxy container for config field {self._field.name} cannot "
            "be pickled; it should be converted to a built-in container before "
            "being assigned to other objects or variables."
        )


class ListField(Field[List[FieldTypeVar]], Generic[FieldTypeVar]):
    """A configuration field (`~lsst.pex.config.Field` subclass) that contains
    a list of values of a specific type.

    Parameters
    ----------
    doc : `str`
        A description of the field.
    dtype : class, optional
        The data type of items in the list. Optional if supplied as typing
        argument to the class.
    default : sequence, optional
        The default items for the field.
    optional : `bool`, optional
        Set whether the field is *optional*. When `False`,
        `lsst.pex.config.Config.validate` will fail if the field's value is
        `None`.
    listCheck : callable, optional
        A callable that validates the list as a whole.
    itemCheck : callable, optional
        A callable that validates individual items in the list.
    length : `int`, optional
        If set, this field must contain exactly ``length`` number of items.
    minLength : `int`, optional
        If set, this field must contain *at least* ``minLength`` number of
        items.
    maxLength : `int`, optional
        If set, this field must contain *no more than* ``maxLength`` number of
        items.
    deprecated : None or `str`, optional
        A description of why this Field is deprecated, including removal date.
        If not None, the string is appended to the docstring for this Field.

    See Also
    --------
    ChoiceField
    ConfigChoiceField
    ConfigDictField
    ConfigField
    ConfigurableField
    DictField
    Field
    RangeField
    RegistryField
    """

    def __init__(
        self,
        doc,
        dtype=None,
        default=None,
        optional=False,
        listCheck=None,
        itemCheck=None,
        length=None,
        minLength=None,
        maxLength=None,
        deprecated=None,
    ):
        if dtype is None:
            raise ValueError(
                "dtype must either be supplied as an argument or as a type argument to the class"
            )
        if dtype not in Field.supportedTypes:
            raise ValueError(f"Unsupported dtype {_typeStr(dtype)}")
        if length is not None:
            if length <= 0:
                raise ValueError(f"'length' ({length}) must be positive")
            minLength = None
            maxLength = None
        else:
            if maxLength is not None and maxLength <= 0:
                raise ValueError(f"'maxLength' ({maxLength}) must be positive")
            if minLength is not None and maxLength is not None and minLength > maxLength:
                raise ValueError(
                    f"'maxLength' ({maxLength}) must be at least as large as 'minLength' ({minLength})"
                )

        if listCheck is not None and not callable(listCheck):
            raise ValueError("'listCheck' must be callable")
        if itemCheck is not None and not callable(itemCheck):
            raise ValueError("'itemCheck' must be callable")

        source = getStackFrame()
        self._setup(
            doc=doc,
            dtype=List,
            default=default,
            check=None,
            optional=optional,
            source=source,
            deprecated=deprecated,
        )

        self.listCheck = listCheck
        """Callable used to check the list as a whole.
        """

        self.itemCheck = itemCheck
        """Callable used to validate individual items as they are inserted
        into the list.
        """

        self.itemtype = dtype
        """Data type of list items.
        """

        self.length = length
        """Number of items that must be present in the list (or `None` to
        disable checking the list's length).
        """

        self.minLength = minLength
        """Minimum number of items that must be present in the list (or `None`
        to disable checking the list's minimum length).
        """

        self.maxLength = maxLength
        """Maximum number of items that must be present in the list (or `None`
        to disable checking the list's maximum length).
        """

    def validate(self, instance):
        """Validate the field.

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Raises
        ------
        lsst.pex.config.FieldValidationError
            Raised if:

            - The field is not optional, but the value is `None`.
            - The list itself does not meet the requirements of the ``length``,
              ``minLength``, or ``maxLength`` attributes.
            - The ``listCheck`` callable returns `False`.

        Notes
        -----
        Individual item checks (``itemCheck``) are applied when each item is
        set and are not re-checked by this method.
        """
        Field.validate(self, instance)
        value = self.__get__(instance)
        if value is not None:
            lenValue = len(value)
            if self.length is not None and not lenValue == self.length:
                msg = f"Required list length={self.length}, got length={lenValue}"
                raise FieldValidationError(self, instance, msg)
            elif self.minLength is not None and lenValue < self.minLength:
                msg = f"Minimum allowed list length={self.minLength}, got length={lenValue}"
                raise FieldValidationError(self, instance, msg)
            elif self.maxLength is not None and lenValue > self.maxLength:
                msg = f"Maximum allowed list length={self.maxLength}, got length={lenValue}"
                raise FieldValidationError(self, instance, msg)
            elif self.listCheck is not None and not self.listCheck(value):
                msg = f"{value} is not a valid value"
                raise FieldValidationError(self, instance, msg)

    def __set__(
        self,
        instance: Config,
        value: Iterable[FieldTypeVar] | None,
        at: Any = None,
        label: str = "assignment",
    ) -> None:
        if instance._frozen:
            raise FieldValidationError(self, instance, "Cannot modify a frozen Config")

        if at is None:
            at = getCallStack()

        if value is not None:
            value = List(instance, self, value, at, label)
        else:
            history = instance._history.setdefault(self.name, [])
            history.append((value, at, label))

        instance._storage[self.name] = value

    def toDict(self, instance):
        """Convert the value of this field to a plain `list`.

        `lsst.pex.config.Config.toDict` is the primary user of this method.

        Parameters
        ----------
        instance : `lsst.pex.config.Config`
            The config instance that contains this field.

        Returns
        -------
        `list`
            Plain `list` of items, or `None` if the field is not set.
        """
        value = self.__get__(instance)
        return list(value) if value is not None else None

    def _compare(self, instance1, instance2, shortcut, rtol, atol, output):
        """Compare two config instances for equality with respect to this
        field.

        `lsst.pex.config.config.compare` is the primary user of this method.

        Parameters
        ----------
        instance1 : `lsst.pex.config.Config`
            Left-hand-side `~lsst.pex.config.Config` instance in the
            comparison.
        instance2 : `lsst.pex.config.Config`
            Right-hand-side `~lsst.pex.config.Config` instance in the
            comparison.
        shortcut : `bool`
            If `True`, return as soon as an **inequality** is found.
        rtol : `float`
            Relative tolerance for floating point comparisons.
        atol : `float`
            Absolute tolerance for floating point comparisons.
        output : callable
            If not None, a callable that takes a `str`, used (possibly
            repeatedly) to report inequalities.

        Returns
        -------
        equal : `bool`
            `True` if the fields are equal; `False` otherwise.

        Notes
        -----
        Floating point comparisons are performed by `numpy.allclose`.
        """
        l1 = getattr(instance1, self.name)
        l2 = getattr(instance2, self.name)
        name = getComparisonName(
            _joinNamePath(instance1._name, self.name), _joinNamePath(instance2._name, self.name)
        )
        if l1 is None or l2 is None:
            return compareScalars(name, l1, l2, output=output)
        if not compareScalars(f"{name} (len)", len(l1), len(l2), output=output):
            return False
        equal = True
        for n, v1, v2 in zip(range(len(l1)), l1, l2, strict=True):
            result = compareScalars(
                f"{name}[{n}]", v1, v2, dtype=self.dtype, rtol=rtol, atol=atol, output=output
            )

            if not result and shortcut:
                return False
            equal = equal and result
        return equal
