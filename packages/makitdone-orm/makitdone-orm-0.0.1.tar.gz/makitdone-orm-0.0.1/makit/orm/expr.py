# coding:utf-8

import typing as t

from makit.orm.base import SqlBase, ModelMetaClass, BaseField
from makit.orm.filters import _Filter


class Join(SqlBase):
    """"""

    def __init__(self, target: ModelMetaClass, *filters: _Filter, join_type='left'):
        self.target = target
        self.filters: t.List[_Filter | str] = list(filters)
        self.join_type = join_type


class OrderField:
    def __init__(self, field: BaseField | str, asc=True):
        self.field = field
        self.asc = asc


class TextExpr(SqlBase):
    def __init__(self, expr: str):
        self.expr = expr
