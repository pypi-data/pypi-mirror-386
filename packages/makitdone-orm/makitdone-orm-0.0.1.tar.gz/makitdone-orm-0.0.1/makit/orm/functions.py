# coding:utf-8

from makit.orm.base import BaseFunc, BaseField


class Max(BaseFunc):
    """

    """


class Min(BaseFunc):
    """

    """


class Avg(BaseFunc):
    """

    """


class Sum(BaseFunc):
    """

    """


class Count(BaseFunc):
    """ COUNT function """

    def __init__(self, field: BaseField = None):
        self.field = field


class Concat(BaseFunc):
    """

    """

    def __init__(self, *fields, seperator=None):
        super().__init__()
        self.fields = fields
        self.seperator = seperator


class Coalesce(BaseFunc):
    """
    合并
    """


class Trim(BaseFunc):
    """

    """


class Length(BaseFunc):
    """

    """


class CompareString(BaseFunc):
    """
    strcmp
    """


class Upper(BaseFunc):
    """ UPPER function """

    def __init__(self, field: BaseField):
        self.field = field


class Lower(BaseFunc):
    """ LOWER function """

    def __init__(self, field: BaseField):
        self.field = field


class Abs(BaseFunc):
    """ ABS function """

    def __init__(self, field: BaseField):
        self.field = field


class Ceil(BaseFunc):
    """ CEIL function """

    def __init__(self, field: BaseField):
        self.field = field


class Floor(BaseFunc):
    """ FLOOR function """

    def __init__(self, field: BaseField):
        self.field = field
