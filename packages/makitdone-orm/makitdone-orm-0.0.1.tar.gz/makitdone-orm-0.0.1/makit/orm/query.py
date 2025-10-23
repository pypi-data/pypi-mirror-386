# coding:utf-8

import typing as t
from copy import copy

from makit.orm.base import BaseQuery, BaseField, ModelMetaClass, SqlValue, SqlBase, Expr
from makit.orm.errors import OrmError
from makit.orm.expr import Join
from makit.orm.fields import ForeignKey, Many, One, ExprField
from makit.orm.filters import _Filter, Equal, NotEqual, GreaterThan, GreaterEqual, LessThan, LessEqual, In, NotIn, Like, \
    NotLike, And, IsNull
from makit.orm.functions import Count
from makit.orm.model import DbModel


class Query(BaseQuery):
    """
    示例：

    """

    def __init__(self, model, **kwargs):
        super().__init__(model=model, **kwargs)
        self._first = False
        self.__fetch_count = None
        self.__check_exists = None
        self._preload_objects = []
        self._output_mode = None
        self._count_field = None

    def use_db(self, db_name: str):
        """强制应用到给定的DB"""
        clone = self._clone()
        clone._db_name = db_name
        return clone

    def table(self, table: str):
        clone = self._clone()
        clone._table = table
        return clone

    def join(self, target: ModelMetaClass | str, *filters: _Filter, join_type='left'):
        clone = self._clone()
        if isinstance(target, str):
            clone._joins.append(Expr(target))
        else:
            if self.__is_model_dbmodel():
                clone._joins.append(Join(target, *filters, join_type=join_type))
            else:
                raise OrmError(f'join target should be DbModel')
        return clone

    def rjoin(self, target: ModelMetaClass | str, *filters: _Filter):
        return self.join(target, *filters, join_type='right')

    def where(self, *args: t.Union[_Filter, Expr, str], **kwargs):
        """
        where查询

        :param args:
        :param kwargs:
        :return:
        """
        clone = self._clone()
        for arg in args:
            if isinstance(arg, str):
                arg = Expr(arg)
            if not clone._filter:
                clone._filter = arg
            else:
                clone._filter = And(clone._filter, arg)
        for key, value in kwargs.items():
            parts = key.split('__')
            token = parts[1] if len(parts) == 2 else None
            field_name = parts[0]  # TODO 支持外键
            if self.__is_model_dbmodel():
                field = self.model.get_meta().field_map.get(field_name)
                if not field:
                    logger = self.executor.logger
                    logger.warn(f'{self.model.__class__} has no field: {field_name}')
                    continue
                f = make_filter_by_token(token, field, value)
            else:
                f = make_filter_by_token(token, field_name, value)
            if f:
                if not clone._filter:
                    clone._filter = f
                else:
                    clone._filter = And(clone._filter, f)
        return clone

    def preload(self, *args: ForeignKey | Many | str, **kwargs):
        """
        示例：
        
        1. query.preload('org')
        2. query.preload('org', 'place')
        3. query.preload('org', order_by=['name'])
        4. query.preload('org', fields=['id', 'name'])
        :param args: 
        :param kwargs: 
        :return: 
        """
        if isinstance(self.model, str):
            raise OrmError('preload only support DbModel')
        if kwargs and len(args) > 1:
            raise OrmError('Only allow one arg if with extra kwargs')
        clone = self._clone()
        for arg in args:
            if isinstance(arg, str):
                field = getattr(clone.model, arg)
                if not isinstance(field, (ForeignKey, Many, One)):
                    raise OrmError(f'{clone.model} has no foreign key: {arg}')
                else:
                    clone._preload_objects.append(field)
            elif isinstance(arg, (ForeignKey, Many, One)):
                clone._preload_objects.append(arg)
            else:
                raise OrmError(f'{arg} should be foreign key')
        return clone

    def group_by(self, *fields: BaseField | str):
        """
        分组

        示例：

        1. query.group_by('gender')
        2. query.group_by(User.gender)
        3. query.group_by('YEAR(`user`.joined_at)')
        4. query.group_by(expr('YEAR(`user`.joined_at)'))
        :param fields:
        :return:
        """
        clone = self._clone()
        for item in fields:
            if isinstance(item, str):
                field = self.model.get_field(item)
                if not field:
                    field = Expr(item)
                clone._groupby.append(field)
            elif isinstance(item, BaseField):
                clone._groupby.append(item)
            else:
                raise OrmError(f'invalid order by: {item}')
        return clone

    def order_by(self, *fields: BaseField | str):
        """
        排序

        示例：

        1. 字段排序：order_by('name')
        2. 倒序：order_by('-name')
        3. 模型字段排序：order_by(User.name)
        4. 按特定表达式排序：order_by('RAND()')
        5. 明确按表达式排序：order_by(expr('RAND()'))

        :param fields:
        :return:
        """
        clone = self._clone()
        for item in fields:
            if isinstance(item, str):
                asc = not item.startswith('-')
                field = self.model.get_field(item)
                if field:
                    clone._orderby.append((field, asc))
                else:
                    clone._orderby.append((Expr(item), True))
            elif isinstance(item, BaseField):
                clone._orderby.append((item, True))
            else:
                raise OrmError(f'invalid order by: {item}')
        return clone

    def limit(self, limit: int):
        clone = self._clone()
        clone._limit = limit
        return clone

    def offset(self, offset: int):
        clone = self._clone()
        clone._offset = offset
        return clone

    def _select_fields(self, *fields: t.Union[BaseField, str]):
        """
        SELECT字段
        :param fields:
        :return:
        """
        clone = self._clone()
        for field in fields:
            if isinstance(field, str):
                if self.__is_model_dbmodel():
                    f = self.model.get_field(field)
                    if f:
                        clone._selected_fields.append(f)
                        continue
                f = ExprField(field)
            else:
                f = field
            clone._selected_fields.append(f)
        return clone

    def values(self, *fields: t.Union[BaseField, str]):
        """

        示例：  
        
        1. query.values('id', 'name')
        2. query.values('*', '-password')
        2. query.values('id', 'name', 'place.name')
        :param fields: 
        :return: 
        """
        # TODO 支持 *, 排除符 -
        clone = self._clone()
        clone._select_fields(*fields)
        clone._output_mode = 'dict'
        return clone

    def values_list(self, *fields: t.Union[BaseField, str]):
        clone = self._clone()
        clone._select_fields(*fields)
        clone._output_mode = 'tuple'
        return clone

    def all(self):
        clone = self._clone()
        return clone

    def first(self):
        clone = self._clone()
        clone = clone.limit(1)
        return clone

    def count(self, field: BaseField | str = None):
        clone = self._clone()
        clone._count_field = Count(field)
        clone.__fetch_count = True
        return clone

    def exists(self):
        """
        查询的数据是否存在
        :return:
        """
        clone = self.count()
        clone.__check_exists = True
        return clone

    def create(self, *instances: DbModel, **kwargs):
        if issubclass(self.model, str) and len(instances) > 0:
            raise OrmError('model created should be DbModel')
        query = CreateQuery(
            model=self.model,
            executor=self.executor,
            table=self._table
        )
        query.create(*instances)
        if kwargs:
            if self.__is_model_dbmodel():
                query.create(self.model(**kwargs))
            else:
                query.data = kwargs
        return query

    def batch_create(self, instance, batch_size):
        """
        批量新增 Create in batch
        """
        instances = []
        for _ in range(batch_size):
            instances.append(instance)
        return self.create(*instances)

    def update(self, *args: str, **kwargs):
        """
        UPDATE

        示例：

        1. query.update(name='new name', age=20)
        2. query.update("`name`='new name'")
        3. query.update(expr('`name`=%s', 'new name'))
        :param args:
        :param kwargs:
        :return:
        """
        query = UpdateQuery(
            model=self.model,
            executor=self.executor,
            table=self._table,
            filter=self._filter,
            joins=self._joins,
            updates=kwargs,
            set_expr_list=list(args)
        )
        return query

    def delete(self):
        """删除"""
        query = DeleteQuery(
            model=self.model,
            executor=self.executor,
            table=self._table,
            filter=self._filter,
        )
        return query

    async def get_or_create(self, **kwargs):
        defaults = kwargs.pop('defaults', {})
        clone = self._clone()
        instance = await clone.where(**kwargs).first()
        not_exists = instance is None
        if not instance:
            info = defaults
            info.update(kwargs)
            instance = await clone.create(**info)
        return instance, not_exists

    async def update_or_create(self, **kwargs):
        defaults = kwargs.pop('defaults', {})
        clone = self._clone()
        instance = await clone.where(**kwargs).first()
        exists = instance is not None
        if instance:
            if defaults:
                await clone.where(**kwargs).update(**defaults)
        else:
            info = defaults
            info.update(kwargs)
            instance = await clone.create(**info)
        return instance, not exists

    def paginate(self, pi: int, ps: int):
        query = PaginationQuery(self, pi, ps)
        return query

    def union(self, query: 'Query'):
        q = UnionQuery(self, query)
        return q

    async def _execute(self):
        if not self._output_mode:
            self._output_mode = 'instance' if self.model else 'dict'
        if isinstance(self.model, ModelMetaClass):
            self._resolve_select_fields()
            if self._count_field:
                self._selected_fields = [self._count_field]
        if self.__check_exists:
            self._selected_fields = [Count()]
        result = await self.executor.exec_query(self)
        if self.__fetch_count:
            count = result.data[0][0]  # count
            if self.__check_exists:
                return count > 0  # exists
            return count
        if self._output_mode == 'tuple':
            if self._limit == 1:
                return result.data[0] if len(result.data) > 0 else None
            return list(result.data)
        field_names = [f.db_column if isinstance(f, (BaseField, ExprField)) else f for f in self._selected_fields]
        output, keys = [], []
        for row in result.data:
            row_data = dict(zip(field_names, row))
            if self._output_mode == 'instance':
                instance = self.model(**row_data)
                output.append(instance)
            else:
                output.append(row_data)
        for item in self._preload_objects:
            if isinstance(item, ForeignKey):
                await self._preload_fk(item, output)
            elif isinstance(item, Many):
                await self._preload_many(item, output)
        if self._limit == 1:
            return None if len(output) == 0 else output[0]
        return output

    async def _preload_fk(self, field: ForeignKey, instances):
        fk_values = set()
        for instance in instances:
            value = getattr(instance, field.db_column, None)
            if value is not None:
                fk_values.add(value)
        if not fk_values:
            return
        fk_values = list(fk_values)

        query = Query(field.related_model, executor=self.executor)
        replated_pk = field.related_model.get_primary_keys()[0]
        query = query.where(replated_pk.in_(fk_values))
        result = await query
        foreign_map = {}
        for item in result:
            key = getattr(item, replated_pk.name)
            foreign_map[key] = item
        for instance in instances:
            value = getattr(instance, field.db_column, None)
            foreign_obj = foreign_map.get(value)
            setattr(instance, field.name, foreign_obj)

    async def _preload_many(self, field: Many, instances):
        pk_values = set()
        pk = field.model.get_primary_keys()[0]
        for instance in instances:
            value = getattr(instance, pk.name, None)
            if value is not None:
                pk_values.add(value)
        if not pk_values:
            return
        pk_values = list(pk_values)
        query = Query(field.through_model, executor=self.executor)
        if len(pk_values) == 0:
            pass
        query = query.where(field.forward_key.in_(pk_values))
        if field.backward_key:
            query = query.preload(field.backward_key)
        result = await query.all()
        if not result:
            return
        for instance in instances:
            value_list = getattr(instance, field.name)
            pk_value = getattr(instance, pk.name)
            for item in result:
                forward_key = getattr(item, field.forward_key.db_column)
                if pk_value == forward_key:
                    if field.backward_key:
                        value_list.append(getattr(item, field.backward_key.name))
                    else:
                        value_list.append(item)

    async def _preload_one(self, field: One):
        pass

    def _clone(self):
        q = copy(self)
        return q

    def _resolve_select_fields(self):
        # 选择所有字段
        fields = self.model.get_meta().fields
        if len(self._selected_fields) == 0:
            for f in fields:
                if isinstance(f, (ForeignKey, Many, One)):
                    continue
                self._selected_fields.append(f)

    def __is_model_dbmodel(self):
        return isinstance(self.model, ModelMetaClass) and issubclass(self.model, DbModel)


class CreateQuery(BaseQuery):
    """"""

    def __init__(self, model: ModelMetaClass | str, **kwargs):
        super().__init__(model=model, **kwargs)
        self.instances = []
        self.returning_fields = []

    def create(self, *instance: DbModel, **kwargs):
        self.instances.extend(instance)
        if kwargs:
            self.instances.append(self.model(**kwargs))
        return self

    async def _execute(self):
        result = await super()._execute()

        if self.returning_fields:
            i = 0
            for instance in self.instances:
                j = 0
                for field in self.returning_fields:
                    value = result.data[i][j]
                    setattr(instance, field, value)
                    j += 1
                i += 1
        if len(self.instances) == 1:
            return self.instances[0]
        return self.instances


class UpdateQuery(BaseQuery):
    """"""


class DeleteQuery(BaseQuery):
    """"""


class ValuesQuery(BaseQuery):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _execute(self):
        result = await self.executor.exec_query(self)


class ValuesListQuery(BaseQuery):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def _execute(self):
        result = await self.executor.exec_query(self)
        data = list(result.data)
        if len(self._selected_fields) == 1:
            # 如果只有一个字段，则flat输出
            data = [item[0] for item in result.data]
        if self._limit == 1:
            return data[0] if len(data) > 0 else None
        return data


class UnionQuery:
    def __init__(self, first, second):
        self.first = first
        self.second = second


class PaginationQuery:
    """分页查询"""

    page_index_key = 'pi'
    page_size_key = 'ps'
    page_list_key = 'list'
    page_total_key = 'total'

    def __init__(self, query: Query, pi: int, ps: int):
        self.query = query
        self.pi = pi
        self.ps = ps

    def __await__(self):
        return self._execute().__await__()

    async def _execute(self):
        if self.pi > 0:
            total = await self.query.count()
            result = await self.query.limit(self.ps).offset((self.pi - 1) * self.ps)
            data = dict()
            data[self.page_index_key] = self.pi
            data[self.page_size_key] = self.ps
            data[self.page_total_key] = total
            data[self.page_list_key] = result
        else:
            data = await self.query
        return data


def make_filter_by_token(token: str, field: BaseField | str, value: t.Any):
    if not isinstance(value, SqlBase):
        value = SqlValue(value)
    if not token and value is None:
        return IsNull(field, True)
    elif not token or token == 'eq':
        return Equal(field, value)
    elif token == 'ne' or token == 'not':
        return NotEqual(field, value)
    elif token == 'gt':
        return GreaterThan(field, value)
    elif token == 'gte':
        return GreaterEqual(field, value)
    elif token == 'lt':
        return LessThan(field, value)
    elif token == 'lte':
        return LessEqual(field, value)
    elif token == 'in':
        return In(field, value) if value.value else None
    elif token == 'notin':
        return NotIn(field, value) if value.value else None
    elif token == 'isnull':
        return IsNull(field, value)
    elif token in ['like', 'contains', 'lk']:
        return Like(field, f'%%{value.value}%%')
    elif token in ['notlike', 'nlk']:
        return NotLike(field, f'%%{value.value}%%')
    elif token in ['prefix', 'start']:
        return NotLike(field, f'{value.value}%%')
    elif token in ['suffix', 'end']:
        return NotLike(field, f'%%{value.value}')
    else:
        raise OrmError('Unknown filter token: {}'.format(token))
