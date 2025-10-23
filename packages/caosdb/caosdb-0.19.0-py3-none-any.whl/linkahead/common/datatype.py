# -*- coding: utf-8 -*-
#
# ** header v3.0
# This file is a part of the LinkAhead Project.
#
# Copyright (C) 2020 IndiScale GmbH
# Copyright (C) 2020 Henrik tom Wörden, IndiScale GmbH
# Copyright (C) 2020 Daniel Hornung (d.hornung@indiscale.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ** end header
#
from __future__ import annotations
import re

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Literal, Union
    from linkahead.common.models import Entity, Container
    DATATYPE = Literal["DOUBLE", "REFERENCE", "TEXT", "DATETIME", "INTEGER", "FILE", "BOOLEAN"]


from ..exceptions import EmptyUniqueQueryError, QueryNotUniqueError

DOUBLE = "DOUBLE"
REFERENCE = "REFERENCE"
TEXT = "TEXT"
DATETIME = "DATETIME"
INTEGER = "INTEGER"
FILE = "FILE"
BOOLEAN = "BOOLEAN"


def LIST(datatype: Union[str, Entity, DATATYPE]) -> str:
    # FIXME May be ambiguous (if name duplicate) or insufficient (if only ID exists).
    datatype = getattr(datatype, "name", datatype)

    return "LIST<" + str(datatype) + ">"


def get_list_datatype(datatype: str, strict: bool = False) -> Union[str, None]:
    """Returns the datatype of the elements in the list.  If it not a list, return None."""
    # TODO Union[str, Entity]
    if not isinstance(datatype, str) or not datatype.lower().startswith("list"):
        if strict:
            raise ValueError(f"Not a list dtype: {datatype}")
        else:
            return None
    pattern = r"^[Ll][Ii][Ss][Tt]((<|&lt;)(?P<dtype1>.*)(>|&gt;)|\((?P<dtype2>.*)\))$"
    match = re.match(pattern, datatype)

    if match and "dtype1" in match.groupdict() and match.groupdict()["dtype1"] is not None:
        return match.groupdict()["dtype1"]

    elif match and "dtype2" in match.groupdict() and match.groupdict()["dtype2"] is not None:
        return match.groupdict()["dtype2"]

    else:
        if strict:
            raise ValueError(f"Not a list dtype: {datatype}")
        else:
            return None


def is_list_datatype(datatype: str) -> bool:
    """ returns whether the datatype is a list """

    return get_list_datatype(datatype) is not None


def is_reference(datatype: str) -> bool:
    """Returns whether the value is a reference

    FILE and REFERENCE properties are examples, but also datatypes that are
    RecordTypes.

    Parameters
    ----------
    datatype : str
               The datatype to check.

    Returns
    -------
    bool
        True if the datatype is a not base datatype or a list of a base datatype.
        Otherwise False is returned.
    """

    if datatype is None:
        raise ValueError("Cannot decide whether datatype is reference if None"
                         " is supplied")

    if datatype in [DOUBLE, BOOLEAN, INTEGER, TEXT, DATETIME]:
        return False
    elif is_list_datatype(datatype):
        return is_reference(get_list_datatype(datatype))  # type: ignore
    else:
        return True


def get_referenced_recordtype(datatype: str) -> str:
    """Return the record type of the referenced datatype.

    Raises
    ------
    ValueError
              In cases where datatype is not a reference, the list does not have
              a referenced record type or the datatype is a FILE.

    Parameters
    ----------
    datatype : str
               The datatype to check.

    Returns
    -------
    str
       String containing the name of the referenced datatype.
    """

    if not is_reference(datatype):
        raise ValueError("datatype must be a reference")

    if is_list_datatype(datatype):
        datatype = get_list_datatype(datatype)  # type: ignore
        if datatype is None:
            raise ValueError("list does not have a list datatype")

    if datatype == FILE:
        raise ValueError(
            "FILE references are not considered references with a record type")

    return datatype


def get_id_of_datatype(datatype: str) -> int:
    """ returns the id of a Record Type

    This is not trivial, as queries may also return children. A check comparing
    names is necessary.

    Parameters
    ----------
    datatype : string
        A datatype, e.g. DOUBLE, or LIST<Person>

    Returns
    -------
    The id of the RecordType with the same name as the datatype.

    Raises
    ------
    QueryNotUniqueError
        If there are more than one entities with the same name as the datatype.
    EmptyUniqueQueryError
        If there is no entity with the name of the datatype.
    """

    from .models import execute_query
    if is_list_datatype(datatype):
        datatype = get_list_datatype(datatype)  # type: ignore
    q = "FIND RECORDTYPE {}".format(datatype)

    # we cannot use unique=True here, because there might be subtypes
    res: Container = execute_query(q)  # type: ignore
    if isinstance(res, int):
        raise ValueError("FIND RECORDTYPE query returned an `int`")
    res: list[Entity] = [el for el in res if el.name.lower() == datatype.lower()]  # type: ignore

    if len(res) > 1:
        raise QueryNotUniqueError(
            "Name {} did not lead to unique result; Missing "
            "implementation".format(datatype))
    elif len(res) != 1:
        raise EmptyUniqueQueryError(
            "No RecordType named {}".format(datatype))

    return res[0].id
