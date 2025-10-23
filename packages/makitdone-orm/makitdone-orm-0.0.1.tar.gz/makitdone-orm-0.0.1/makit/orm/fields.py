# coding:utf-8

import base64
import json
import re
import typing as t
import uuid
from datetime import datetime
from functools import cached_property

from makit.orm.base import BaseField, BaseQuery, ModelMetaClass, SqlValue, FK_CASCADE, FK_RESTRICT
from makit.orm.errors import OrmError, OrmValueError
from makit.orm.filters import Equal, GreaterThan, GreaterEqual, LessThan, LessEqual, In, Like
from makit.orm.functions import Abs, Ceil, Floor
from makit.orm.model import DbModel


class ExprField:
    def __init__(self, expr: str):
        self.expr = expr

    @cached_property
    def db_column(self):
        parts = self.expr.rsplit(' ', maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip('`')
        parts = self.expr.rsplit('.', maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip('`')
        return None


class _NumberField(BaseField):
    def __abs__(self):
        return Abs(self)

    def abs(self) -> Abs:
        return Abs(self)

    def __ceil__(self):
        return Ceil(self)

    def ceil(self):
        return Ceil(self)

    def __floor__(self):
        return Floor(self)

    def floor(self):
        return Floor(self)


class FilterField(BaseField):
    def __eq__(self, other) -> Equal:
        return Equal(self, other)

    def __gt__(self, other) -> GreaterThan:
        return GreaterThan(self, other)

    def __ge__(self, other) -> GreaterEqual:
        return GreaterEqual(self, other)

    def __lt__(self, other) -> LessThan:
        return LessThan(self, other)

    def __le__(self, other) -> LessEqual:
        return LessEqual(self, other)

    def in_(self, expr: t.Union['BaseQuery', list]):
        return In(self, expr)


class DbField(FilterField):
    """"""


class _StrField(DbField):
    collate = 'utf8mb4_general_ci'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_strip = kwargs.get('auto_strip')

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def to_db_value(self, value):
        if self.auto_strip:
            value = value.strip()
        return super().to_db_value(value)


class UUID(_StrField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cached_property
    def db_type(self):
        return f"VARCHAR({len(str(uuid.uuid4()))})"

    @property
    def db_default(self):
        if self.pk:
            return 'uuid()'
        return None

    def validate(self, value):
        super().validate(value)
        try:
            if value is not None:
                uuid.UUID(value)
        except ValueError:
            raise OrmValueError(f'invalid uuid: {value}')

    def default_value(self):
        if self.pk:
            return str(uuid.uuid4())
        value = super().default_value()
        if value is None:
            return value
        return str(value)


class String(_StrField):

    def __init__(
            self,
            length,
            **kwargs
    ):
        super().__init__(length, **kwargs)
        self.length = length
        self.allow_blank = kwargs.get('blank', True)

    @property
    def db_type(self):
        return f"VARCHAR({self.length})"

    def validate(self, value):
        super().validate(value)
        if not self.allow_blank and value == '':
            raise OrmValueError(f'field value can not be empty: {self.model.__name__}.{self.name}')
        if value and len(value) > self.length:
            raise OrmValueError(f'field "{self.model.__name__}.{self.name}" value length can not be '
                                f'large than: {self.length}')

    def prefix(self, prefix: str) -> Like:
        return Like(self, SqlValue(prefix + '%'))

    def suffix(self, suffix: str) -> Like:
        return Like(self, SqlValue('%' + suffix))

    def contains(self, sub) -> Like:
        return Like(self, '%' + sub + '%')

    def like(self, expression: str) -> Like:
        return Like(self, SqlValue(expression))

    def in_(self, expr: BaseQuery | list) -> In:
        """"""
        if isinstance(expr, list):
            return In(self, SqlValue(expr))
        return In(self, expr)


class BigInt(_NumberField):
    """"""

    def __init__(self, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk:
            kwargs['auto_increment'] = True
        super().__init__(*args, **kwargs)

    def in_(self, expr: t.Union['BaseQuery', list]):
        return In(self, expr)

    @property
    def db_type(self):
        return f'BIGINT'


class Int(_NumberField):
    """"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.length = kwargs.get('length', 11)

    @property
    def db_type(self):
        return f'INT({self.length})'


class SmallInt(_NumberField):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def db_type(self):
        return 'SMALLINT'


class TinyInt(_NumberField):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def db_type(self):
        return 'TINYINT'


class Float(_NumberField):
    """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accuracy = kwargs.get('accuracy')

    @property
    def db_type(self):
        return 'FLOAT'


class Boolean(DbField):

    @property
    def db_type(self):
        return 'TINYINT(1)'

    def to_py_value(self, value):
        if value == 1:
            return True
        return False

    def to_db_value(self, value):
        if value in [1, True, 'true']:
            return 1
        return 0


class Text(_StrField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = kwargs.get('size')

    @property
    def db_type(self):
        if self.size == 'default':
            return 'TEXT'
        elif self.size == 'tiny':
            return 'TINYTEXT'
        elif self.size == 'medium':
            return 'MEDIUMTEXT'
        else:
            return 'LONGTEXT'


class Json(Text):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict())
        super().__init__(**kwargs)

    def to_db_value(self, value):
        if not value:
            value = self.default_value()
        return json.dumps(value)

    def to_py_value(self, value):
        if value is None:
            value = self.default_value()
        if isinstance(value, str):
            return json.loads(value)
        elif isinstance(value, (list, dict)):
            return value
        raise OrmValueError(f'Invalid value for field: {self.model.__name__}.{self.name}')


# class Enum(BaseField):
#     def __init__(self, db_column=None, default=None):
#         super().__init__(db_column=db_column, default=default)


# class IntEnum(BaseField):
#     def __init__(self, db_column=None, default=None):
#         super().__init__(db_column=db_column, default=default)


class DateTime(DbField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_now = kwargs.get('auto_now', False)
        self.update_now = kwargs.get('update_now', False)

    @property
    def db_type(self):
        return 'DATETIME'

    def default_value(self):
        if self.auto_now:
            return datetime.now()
        return None


class Date(DbField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def db_type(self):
        return 'DATE'


class Time(DbField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def db_type(self):
        return 'TIME'


class Timestamp(DbField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def db_type(self):
        return 'TIMESTAMP'


class Blob(DbField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def db_type(self):
        return 'BLOB'


class Binary(DbField):
    """"""


class Image(DbField):
    """

    """

    @property
    def db_type(self):
        return 'MEDIUMBLOB'

    def to_db_value(self, value):
        if value:
            value = value
        else:
            value = ''
        return value

    def to_py_value(self, value):
        if value:
            value = super().to_py_value(value)
            encoded_bytes = base64.b64encode(value)
            return encoded_bytes.decode('utf-8')
        return value


class File(DbField):

    def __init__(self, stream, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = stream
        self.filename = kwargs.get('filename')  # 存储名称
        self.compressed = kwargs.get('compressed')  # 是否压缩存储

    def validate(self, value):
        pass

    def compress(self):
        """
        压缩
        """
        pass


class ImageFile(File):
    """
    图片字段
    """


class Relation(FilterField):
    """关系字段"""


class ForeignKey(FilterField):
    """外键"""

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._related_model = model
        self.on_update = kwargs.get('on_update', FK_CASCADE)
        self.on_delete = kwargs.get('on_delete', FK_RESTRICT)

    @cached_property
    def related_model(self):
        model = self._related_model
        if isinstance(model, str):
            meta = getattr(self.model, '_meta')
            model_key = '.'.join([meta.db_name, model])
            model = ModelMetaClass.model_map.get(model_key)
        if not model:
            raise OrmError(f'Invalid model for ForeignKey: {self.model.__name__}.{self.name}')
        return model

    @cached_property
    def related_pk(self) -> BaseField:
        pks = getattr(self.related_model, '_meta').primary_keys
        if not pks:
            raise OrmError(f"Model '{self.related_model.__name__}' should have primary key")
        if len(pks) > 1:
            raise OrmError(f"Model '{self.related_model.__name__}' should only have one primary key")
        return pks[0]

    @cached_property
    def db_column(self):
        return f'{self.name}_{self.related_pk.name}'

    @cached_property
    def field(self):
        name = self.db_column
        field = getattr(self.model, name, None)
        if not field:
            field: BaseField = object.__new__(self.related_pk.__class__)
            field.__init__(*self.related_pk.args, **self.kwargs)
            setattr(field, 'name', self.db_column)
            setattr(field, '_model', self.model)
            setattr(field, '_db_column', None)
            setattr(self.model, name, field)
        return field


def model_field(model: DbModel, key: str):
    meta = getattr(model, '_meta')
    parts = key.split('.', maxsplit=1)
    if len(parts) > 1:
        name = parts[0]
        extra = parts[1]
        field = meta.field_map.get(name)
        if isinstance(field, ForeignKey):
            return model_field(field.model, extra)
        else:
            raise OrmError(f'{model} has no field: {name}')
    else:
        field = meta.field_map.get(key)
        return field


class Many(FilterField):
    def __init__(self, target: str):
        super().__init__()
        self._target = target

    @cached_property
    def through_model(self):
        if not self._target:
            raise OrmError('Invalid target!')
        parts = self._target.split('.')
        model_name = parts[0]
        model_key = f"{self.model.__db__}.{model_name}"
        return ModelMetaClass.model_map.get(model_key)

    @cached_property
    def forward_key(self):
        fks: t.List[ForeignKey] = self.through_model.get_meta().foreign_keys
        for fk in fks:
            if fk.related_model == self.model:
                return fk

    @cached_property
    def backward_key(self):
        parts = self._target.split('.')
        if len(parts) == 1:
            return None
        fks: t.List[ForeignKey] = self.through_model.get_meta().foreign_keys
        for fk in fks:
            if fk.related_model != self.model:
                return fk

    def default_value(self):
        return []


class One(FilterField):
    """一对一"""

    def __init__(self, model):
        super().__init__()
        self._model = model
