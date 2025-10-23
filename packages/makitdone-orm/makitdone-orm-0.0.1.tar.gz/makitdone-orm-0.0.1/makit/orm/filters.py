# coding:utf-8

import typing as t

from makit.orm.base import BaseFilter, SqlBase


class _Filter(BaseFilter):
    """"""
    token = None

    def __init__(self, left: SqlBase, right: t.Any):
        super().__init__()
        self.left = left
        self.right = right

    def __and__(self, other: '_Filter'):
        if isinstance(other, And):
            other.filters.append(self)
            return other
        return And(self, other)

    def __or__(self, other: '_Filter'):
        if isinstance(other, Or):
            other.filters.append(self)
            return other
        return Or(self, other)


class Equal(_Filter):
    token = '='


class NotEqual(_Filter):
    token = '<>'


class GreaterThan(_Filter):
    token = '>'


class GreaterEqual(_Filter):
    token = '>='


class LessThan(_Filter):
    token = '<'


class LessEqual(_Filter):
    token = '<='


class Like(_Filter):
    """"""
    token = 'LIKE'


class NotLike(_Filter):
    token = 'NOT LIKE'


class In(_Filter):
    token = 'IN'


class NotIn(_Filter):
    token = 'NOT IN'


class IsNull(_Filter):
    """"""


class And(BaseFilter):
    """ and expression """

    def __init__(self, *filters: BaseFilter):
        super().__init__()
        self.filters: t.List[BaseFilter] = []
        for f in filters:
            self.__and__(f)

    def __and__(self, other: BaseFilter):
        if isinstance(other, And):
            self.filters.extend(other.filters)
        else:
            self.filters.append(other)
        return self

    def __or__(self, other: BaseFilter):
        return Or(self, other)


class Or(BaseFilter):
    """ or expression"""
    token = 'OR'

    def __init__(self, *filters: BaseFilter):
        super().__init__()
        self.filters = []
        for f in filters:
            self.__or__(f)

    def __and__(self, other: BaseFilter):
        return And(self, other)

    def __or__(self, other: BaseFilter):
        if isinstance(other, Or):
            self.filters.extend(other.filters)
        else:
            self.filters.append(other)
        return self
