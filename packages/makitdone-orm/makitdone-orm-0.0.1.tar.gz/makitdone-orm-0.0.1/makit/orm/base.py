# coding:utf-8

import re
import typing as t
from copy import copy
from functools import cached_property

from makit.orm.errors import OrmValueError


class SqlBase:
    """"""


class Expr(SqlBase):
    """ SQL表达式 """

    def __init__(self, expr: str, *args):
        self.expr = expr
        self.args = args


class SqlValue(SqlBase):
    def __init__(self, value: t.Any):
        self.value = value


class BaseFilter(SqlBase):
    """"""


class BaseFunc(SqlBase):
    """"""


class BaseField(SqlBase):
    """"""

    def __init__(self, *args, **kwargs):
        self.name = None
        self._model = None
        self.args = args
        self.kwargs = kwargs
        self.json = kwargs.get('json')  # 控制序列化，如果为False，序列化时予以忽略
        self._db_column = kwargs.get('db_column')
        self.pk = pk = kwargs.get('pk', False)
        self.nullable = kwargs.get('null')
        if pk:
            self.nullable = False
        self.default = kwargs.get('default')
        self.comment = kwargs.get('comment')
        self.auto_increment = kwargs.get('auto_increment', False)  # 是否自动累加
        self.collate = kwargs.get('collate', None)
        self.index = kwargs.get('index', False)
        self.unique = kwargs.get('unique', False)
        self._json_encode = None
        self._json_decode = None

    @property
    def model(self):
        return self._model

    @property
    def tablename(self):
        meta = getattr(self.model, '_meta')
        return meta.tablename

    @property
    def db_column(self):
        return self._db_column or self.name

    @property
    def db_type(self):
        raise NotImplementedError()

    @property
    def db_default(self):
        return None

    def default_value(self):
        if self.default and callable(self.default):
            return self.default()
        return self.default

    def to_db_value(self, value):
        if not self.nullable and value is None:
            value = self.default_value()
        self.validate(value)
        return value

    def to_py_value(self, value):
        return value

    def validate(self, value):
        if not self.nullable and value is None:
            raise OrmValueError(f'field value can not be None: {self.name}')

    def __eq__(self, other) -> BaseFilter:
        raise NotImplementedError

    def in_(self, expr: t.Union['BaseQuery', list]):
        raise NotImplementedError

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'


class MetaInfo:

    def __init__(self):
        self.db_name: str | None = None
        self.app_name: str | None = None
        self.model = None
        self.abstract = False
        self.tablename = None
        self._field_map: dict = {}

    @cached_property
    def primary_keys(self):
        keys = []
        for name, field in self._field_map.items():
            if field.pk:
                keys.append(field)
        return keys

    @cached_property
    def fields(self):
        fields = []
        for name, field in self._field_map.items():
            if field.__class__.__name__ == 'ForeignKey':
                fields.append(field.field)
            fields.append(field)
        return fields

    @cached_property
    def field_names(self):
        names = []
        for name, field in self._field_map.items():
            if field.__class__.__name__ == 'ForeignKey':
                names.append(field.db_column)
            else:
                names.append(field.name)
        return names

    @cached_property
    def field_map(self) -> t.Dict[str, BaseField]:
        fmap = dict(**self._field_map)
        for name, field in self._field_map.items():
            if field.__class__.__name__ == 'ForeignKey':
                f = field.field
                fmap[f.name] = field.field
        return fmap

    @cached_property
    def foreign_keys(self):
        fields = []
        for name, field in self._field_map.items():
            if field.__class__.__name__ == 'ForeignKey':
                fields.append(field)
        return fields

    def add_field(self, field: BaseField):
        self._field_map[field.name] = field

    def __iter__(self):
        for name, field in self._field_map.items():
            yield name, field


class ModelMetaClass(type):
    all = []
    model_map = dict()

    def __new__(mcs, name, bases, attrs):
        new_class = super().__new__(mcs, name, bases, attrs)
        meta = MetaInfo()
        meta.db_name = attrs.get('__db__')
        meta.abstract = attrs.get('__abstract__', False)
        meta.tablename = attrs.get('__tablename__', str_uncamel(name))
        for base in bases:
            meta_info: MetaInfo = getattr(base, '_meta', None)
            if not meta_info:
                continue

            if meta_info.db_name and not meta.db_name:
                meta.db_name = meta_info.db_name

            for _, field in meta_info:
                cloned_field = copy(field)
                setattr(cloned_field, '_model', new_class)
                meta.add_field(cloned_field)
        for name, v in attrs.items():
            if not isinstance(v, BaseField):
                continue
            setattr(v, '_model', new_class)
            v.name = name
            meta.add_field(v)
        meta.model = new_class
        setattr(new_class, '_meta', meta)
        if not meta.abstract:
            ModelMetaClass.all.append(new_class)
            ModelMetaClass.model_map[f"{meta.db_name}.{new_class.__name__}"] = new_class
        return new_class

    def __iter__(self):
        meta: MetaInfo = getattr(self, '_meta')
        for f in meta.fields:
            yield f


def str_uncamel(s: str, sep='_'):
    """
    将驼峰风格字符串转换为下划线风格
    :param s:
    :param sep:
    :return:
    """
    s = re.sub('([a-z]+)(?=[A-Z])', r'\1' + sep, s)
    return s.lower()


class BaseQuery(SqlBase):
    """"""

    def __init__(self, **kwargs):
        self.model = kwargs.pop('model')
        self.executor = kwargs.get('executor')
        self._db_name = kwargs.get('db_name', '')
        self._table = kwargs.get('table')
        self._filter = kwargs.get('filter')
        self._selected_fields = kwargs.get('select_fileds', [])
        self._joins = kwargs.get('joins', [])
        self._orderby: t.List[t.Tuple[BaseField | Expr, bool]] = kwargs.get('orderby', [])
        self._groupby: t.List[BaseField | Expr] = kwargs.get('groupby', [])
        self._limit = kwargs.get('limit', None)
        self._offset = kwargs.get('offset')
        self._updates = kwargs.get('updates')
        self._set_expr_list = kwargs.get('set_expr_list')

    @property
    def expressions(self):
        expr = dict()
        if self._db_name:
            expr['db_name'] = self._db_name
        if self._table:
            expr['table'] = self._table
        if self._selected_fields:
            expr['select_fields'] = self._selected_fields
        if self._joins:
            expr['joins'] = self._joins
        if self._filter:
            expr['filter'] = self._filter
        if self._orderby:
            expr['orderby'] = self._orderby
        if self._groupby:
            expr['groupby'] = self._groupby
        if self._limit:
            expr['limit'] = str(self._limit)
        if self._offset:
            expr['offset'] = str(self._offset)
        if self._updates:
            expr['updates'] = self._updates
        if self._set_expr_list:
            expr['set_expr_list'] = self._set_expr_list
        return expr

    def __await__(self):
        return self._execute().__await__()

    async def _execute(self):
        return await self.executor.exec_query(self)


FK_CASCADE = "CASCADE"
FK_RESTRICT = "RESTRICT"
FK_SET_NULL = "SET NULL"
FK_SET_DEFAULT = "SET DEFAULT"
FK_NO_ACTION = "NO ACTION"


class BaseClient:
    """"""


class BaseExecutor:
    """"""

    @property
    def in_transaction(self) -> bool:
        return False

    async def begin(self):
        raise NotImplementedError

    async def rollback(self):
        raise NotImplementedError

    async def commit(self):
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError

    def is_closed(self) -> bool:
        raise NotImplementedError

    async def exec_sql(self, sql: str, *args):
        raise NotImplementedError

    async def field_exists(self, field) -> bool:
        raise NotImplementedError

    async def get_db_tables(self):
        raise NotImplementedError

    async def get_db_columns(self):
        raise NotImplementedError

    async def drop_constraints(self, model: ModelMetaClass = None):
        raise NotImplementedError


class SqlBuilder:
    def sql_insert(self, query: BaseQuery) -> str:
        raise NotImplementedError

    def sql_select(self, query: BaseQuery) -> str:
        raise NotImplementedError

    def sql_update(self, query: BaseQuery) -> str:
        raise NotImplementedError

    def sql_delete(self, query: BaseQuery) -> str:
        raise NotImplementedError

    def sql_create_table(self, model) -> str:
        raise NotImplementedError

    def sql_alter_table_comment(self, model: ModelMetaClass) -> str:
        raise NotImplementedError

    def sql_add_column(self, field: BaseField) -> str:
        raise NotImplementedError

    def sql_alter_column(self, field: BaseField) -> str:
        raise NotImplementedError

    def sql_add_fk_constraint(self, field: BaseField) -> str:
        raise NotImplementedError
