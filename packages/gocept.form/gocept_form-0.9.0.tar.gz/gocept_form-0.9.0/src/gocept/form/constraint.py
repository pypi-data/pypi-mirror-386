# Copyright (c) 2007-2008 gocept gmbh & co. kg
# See also LICENSE.txt
"""Tools for schema field constraints."""


def _all(list):
    """Emulates Python 2.5's all() function."""
    return bool(len([x for x in list if x]))


def all(*constraints):
    return lambda value: _all([c(value) for c in constraints])
