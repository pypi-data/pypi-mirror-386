# coding:utf-8

import inspect
import time
import typing as t
from datetime import datetime
from functools import cached_property

import aiomysql
from aiomysql import Pool, Cursor
from pymysql import converters

from makit.orm import utils
from makit.orm.base import BaseClient, BaseExecutor, BaseQuery, SqlBase, BaseField, SqlValue, BaseFunc, ModelMetaClass, \
    MetaInfo, BaseFilter, SqlBuilder, Expr
from makit.orm.errors import OrmError
from makit.orm.expr import Join
from makit.orm.fields import ForeignKey, Boolean, DateTime, UUID, Many, One, DbField, ExprField
from makit.orm.filters import _Filter, And, Or, IsNull
from makit.orm.functions import Count
from makit.orm.model import DbModel
from makit.orm.query import Query, CreateQuery, UpdateQuery, DeleteQuery


class MySqlResult:
    """ SQL 执行结果 """

    def __init__(self, **kwargs):
        self.data = kwargs.get('data')
        self.rowcount = kwargs.get('rowcount', 0)
        self.rownumber = kwargs.get('rownumber')
        self.returning = kwargs.get('returning', None)


class MysqlClient(BaseClient):
    """"""

    def __init__(self, config: dict, **kwargs):
        self.config = config
        self._pool: t.Optional[Pool] = None
        self.logger = kwargs.get('logger')
        self.loop = kwargs.get('loop')

    @cached_property
    def db_name(self):
        return self.config['db']

    @cached_property
    def debug(self):
        debug = self.config.get('debug', 'false').lower()
        return debug == 'true'

    async def create_pool(self) -> Pool:
        if self._pool:
            return self._pool
        db = self.config.get('db')
        if not db:
            raise OrmError('missing db config item: db')
        pool = aiomysql.create_pool(
            minsize=self.config.get('minsize', 5),
            maxsize=self.config.get('maxsize', 50),
            pool_recycle=self.config.get('pool_recycle', 3600),
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 3306),
            user=self.config.get('user', 'root'),
            password=self.config.get('pwd', 'root'),
            db=db,
            loop=self.loop,
            connect_timeout=self.config.get('connect_timeout', 5),
        )
        self._pool = await pool
        return self._pool

    def close(self):
        if self._pool:
            self._pool.wait_closed()

    def release(self, conn):
        if self._pool:
            self._pool.release(conn)

    async def get_connection(self):
        pool = await self.create_pool()
        conn = await pool.acquire()
        return conn


class MysqlExecutor(BaseExecutor):

    def __init__(self, conn: aiomysql.Connection, cursor: aiomysql.Cursor, **kwargs):
        self.client: MysqlClient | None = None
        self._conn = conn
        self._cursor = cursor
        self.logger = kwargs.get('logger')
        self._closing = False

    @cached_property
    def sql_builder(self):
        return MysqlBuilder(self.client.config, self._cursor)

    @property
    def in_transaction(self) -> bool:
        return self._conn.get_transaction_status()

    async def begin(self):
        await self._conn.begin()

    async def rollback(self):
        await self._conn.rollback()

    async def commit(self):
        await self._conn.commit()

    async def auto_commit(self):
        await self._conn.autocommit(True)

    async def close(self):
        if not self._closing:
            self._closing = True
            await self._cursor.close()
            await self._conn.ensure_closed()
            self.client.release(self._conn)
            self._closed = True

    def is_closed(self):
        return self._cursor.closed and self._conn.closed

    async def exec_query(self, query: BaseQuery):
        sql = self.sql_builder.sql_query(query)
        if not sql:
            raise OrmError('invalid query')
        return await self.exec_sql(sql)

    async def exec_sql(self, sql: str, *args):
        try:
            start = time.time()
            # sql = self.sql_builder.cursor.mogrify(sql, args)
            await self._cursor.execute(sql, args if args else None)
            cost = time.time() - start
            if self.client.debug and self.logger:
                self.logger.debug(f'{round(cost * 1000, 3)}ms,' + sql)
            output = await self._cursor.fetchall()
            result = MySqlResult(
                rowcount=self._cursor.rowcount,
                rownumber=self._cursor.rownumber,
                lastrowid=self._cursor.lastrowid,
                arraysize=self._cursor.arraysize,
                description=self._cursor.description,
                data=output
            )
        except Exception as e:
            if self.client.debug and self.logger:
                self.logger.debug('fail: ' + sql)
            raise e
        return result

    async def drop_constraints(self, model: ModelMetaClass = None):
        """移除模型所有的约束"""
        # 获取模型表的约束
        db_name = self.client.db_name
        tablename = utils.tablename(model)
        q = Query('STATISTICS', executor=self).use_db('information_schema').where(
            f"`TABLE_SCHEMA`='{db_name}'",
            # f"`INDEX_NAME` <> 'PRIMARY'"
        ).values_list('INDEX_NAME')
        if model:
            q = q.where(f"`TABLE_NAME`='{tablename}'")
        result = await q
        sql_list = []
        for name, in result:
            if name == 'PRIMARY':
                continue
            name = name.lower()
            if name.startswith('fk_'):
                sql_list.append(f"ALTER TABLE `{tablename}` DROP FOREIGN KEY `{name}`;")
            sql_list.append(f"ALTER TABLE `{tablename}` DROP INDEX `{name}`;")
        if sql_list:
            sql = '\n'.join(sql_list)
            await self.exec_sql(sql)

    async def field_exists(self, field) -> bool:
        db_name = self.client.db_name
        exists = await Query('COLUMNS', executor=self).use_db('information_schema').where(
            f"`TABLE_SCHEMA`='{db_name}'",
            f"`TABLE_NAME`='{utils.tablename(field.model)}'",
            f"`COLUMN_NAME`='{field.db_column}'"
        ).exists()
        return exists

    async def get_db_tables(self):
        db_name = self.client.db_name
        tables = await Query('TABLES', executor=self).use_db('information_schema').where(
            f"`TABLE_SCHEMA`='{db_name}'"
        ).values_list('TABLE_NAME')
        return [tablename for tablename, in tables]

    async def get_db_columns(self):
        db_name = self.client.db_name
        cols = await Query('COLUMNS', executor=self).use_db('information_schema').where(
            f"`TABLE_SCHEMA`='{db_name}'"
        ).values_list('TABLE_NAME', 'COLUMN_NAME')
        return cols


class MysqlBuilder(SqlBuilder):
    """"""

    def __init__(self, config, cursor):
        self.config = config or {}
        self.cursor: Cursor = cursor
        self._schema_db = 'information_schema'

    def _expr_groupby_fields(self, query):
        groupby: t.List[BaseField | Expr] = query.expressions.get('groupby')
        if not groupby:
            return None
        field_strs = []
        for field in groupby:
            if isinstance(field, BaseField):
                fstr = self._expr_field(field)
            else:
                fstr = field.expr
            field_strs.append(fstr)
        return ', '.join(field_strs)

    def _expr_orderby_fields(self, query):
        orderby: t.List[t.Tuple[BaseField | Expr, bool]] = query.expressions.get('orderby')
        if not orderby:
            return None
        field_strs = []
        for field, asc in orderby:
            if isinstance(field, BaseField):
                fstr = self._expr_field(field)
            else:
                fstr = field.expr
            if not asc:
                fstr += ' DESC'
            field_strs.append(fstr)
        return ', '.join(field_strs)

    def _expr_field(self, field: BaseField):
        return f'{self.expr_tablename(field.model)}.`{field.db_column}`'

    # ---------------------------------------------

    @classmethod
    def field_db_type(cls, field: BaseField) -> str:
        if isinstance(field, Boolean):
            return 'TINYINT(1)'
        return field.db_type

    @classmethod
    def expr_field_db_default(cls, field: BaseField):
        if isinstance(field, DateTime):
            if field.auto_now:
                return 'CURRENT_TIMESTAMP()'
            elif field.update_now:
                return 'NULL ON UPDATE CURRENT_TIMESTAMP()'
        elif isinstance(field, UUID):
            if field.pk:
                return 'uuid()'
        return None

    def sql_query(self, query: BaseQuery) -> str:
        if isinstance(query, Query):
            return self.sql_select(query)
        elif isinstance(query, CreateQuery):
            return self.sql_insert(query)
        elif isinstance(query, UpdateQuery):
            return self.sql_update(query)
        elif isinstance(query, DeleteQuery):
            return self.sql_delete(query)
        raise OrmError('invalid query type')

    def sql_select(self, query: Query) -> str:
        expr_parts = ['SELECT']
        expressions = query.expressions
        if 'select_fields' in expressions:
            fields = expressions.get('select_fields')
            expr_parts.append(', '.join([self.expr_field(f) for f in fields]))
            expr_parts.append('FROM')
            expr_parts.append(self.expr_tablename(query))
        else:
            raise OrmError('no fields selected')
        joins = expressions.get('joins')
        if joins:
            for j in joins:
                expr_parts.append(self.expr(j))
        where_expr = self.expr_where(query)
        if where_expr:
            expr_parts.append(where_expr)
        groupby = self._expr_groupby_fields(query)
        if groupby:
            expr_parts.append('GROUP BY')
            expr_parts.append(groupby)
        orderby = self._expr_orderby_fields(query)
        if orderby:
            expr_parts.append('ORDER BY')
            expr_parts.append(orderby)
        limit = expressions.get('limit')
        if limit:
            expr_parts.append(f'LIMIT {limit}')
        offset = expressions.get('offset')
        if offset:
            expr_parts.append(f'OFFSET {offset}')
        return ' '.join(expr_parts) + ';'

    def sql_insert(self, query: CreateQuery) -> str:
        if issubclass(query.model, DbModel):
            meta = query.model.get_meta()
            tablename = meta.tablename
            expr_parts = ['INSERT INTO', tablename]
            fields = meta.fields
            field_expr = ''
            values_expr_list = []
            returning_expr = []
            for instance in query.instances:
                value_expr = []
                field_names = []
                for field in fields:
                    if isinstance(field, (ForeignKey, Many, One)):
                        continue
                    if field.auto_increment:
                        if field.name not in query.returning_fields:
                            query.returning_fields.append(field.name)
                            returning_expr.append(self.expr_field(field))
                        continue
                    if not field_expr:
                        field_names.append(self.expr_field(field))
                    value = getattr(instance, field.name)
                    if value is None:
                        value = field.default_value()
                    value = field.to_db_value(value)
                    value_expr.append(self.expr_value(value))
                if not field_expr:
                    field_expr = f"({', '.join(field_names)})"
                values_expr_list.append(f'({", ".join(value_expr)})')
            expr_parts.append(field_expr)
            expr_parts.append('VALUES')
            expr_parts.append(', '.join(values_expr_list))
            if query.returning_fields:
                expr_parts.append("RETURNING")
                expr_parts.append(', '.join(returning_expr))
            return ' '.join(expr_parts) + ';'
        else:
            tablename = query._table or query.model
            expr_parts = ['INSERT INTO', tablename]
            return ''  # TODO

    def sql_update(self, query: UpdateQuery) -> str:
        expressions = query.expressions
        field_expr = expressions.get('set_expr_list', [])
        updates = expressions.get('updates', {})
        if not updates and not field_expr:
            return ''
        tablename = self.expr_tablename(query)
        expr_parts = ['UPDATE', tablename]
        joins = expressions.get('joins')
        if joins:
            for j in joins:
                expr_parts.append(self.expr(j))

        meta_info: MetaInfo = getattr(query.model, '_meta')
        field_map = meta_info.field_map
        for key, value in updates.items():
            field = field_map.get(key)
            if not isinstance(field, DbField):
                continue
            value = field.to_db_value(value)
            if not field:
                continue
            field_expr.append(f'{self.expr_field(field)} = {self.expr_value(value)}')
        expr_parts.append('SET')
        expr_parts.append(', '.join(field_expr))
        where_expr = self.expr_where(query)
        if where_expr:
            expr_parts.append(where_expr)
        sql = ' '.join(expr_parts) + ';'
        return sql

    def sql_delete(self, query) -> str:
        tablename = self.expr_tablename(query)
        parts = ['DELETE FROM', tablename]
        where_expr = self.expr_where(query)
        if where_expr:
            parts.append(where_expr)
        return ' '.join(parts) + ';'

    def sql_add_fk_constraint(self, field: ForeignKey) -> str:
        constraint_name = f'`fk_{field.tablename}_{field.name}`'
        related_model = field.related_model
        related_model_name = utils.tablename(related_model)
        related_fk_pks = related_model.get_primary_keys()
        if not related_fk_pks:
            raise OrmError(f'Unknown primary key: {related_model_name}')
        related_fk_pk = related_fk_pks[0]
        parts = [
            'ALTER TABLE',
            utils.tablename(field.model),
            'ADD CONSTRAINT',
            constraint_name,
            'FOREIGN KEY',
            f'(`{field.db_column}`)',
            'REFERENCES',
            related_model_name,
            f'(`{related_fk_pk.db_column}`)',
            f'ON UPDATE {field.on_update} ON DELETE {field.on_delete};'
        ]
        if field.index:
            pass
        if field.unique:
            pass
        return ' '.join(parts)

    def expr_value(self, value: t.Any) -> t.Any:
        if value is None:
            return 'NULL'
        if isinstance(value, bytes):
            ret = converters.escape_bytes(value)
            return ret
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, datetime):
            return f"'{str(value)}'"
        elif isinstance(value, list):
            expr = ', '.join([self.expr_value(v) for v in value])
            return f'({expr})'
        elif isinstance(value, SqlValue):
            return self.expr_value(value.value)
        elif isinstance(value, Expr):
            return value.expr
        return str(value)

    def expr_func(self, f: BaseFunc):
        if isinstance(f, Count):
            if not f.field:
                return 'COUNT(1)'
            return f'COUNT({self.expr(f.field)})'
        return None

    def expr_field(self, field: BaseField | BaseFunc | str):
        if isinstance(field, BaseField):
            return f'{self.expr_tablename(field.model)}.`{field.db_column}`'
        elif isinstance(field, BaseFunc):
            return self.expr_func(field)
        elif isinstance(field, ExprField):
            return field.expr
        return field

    @classmethod
    def expr_tablename(cls, target: BaseQuery | ModelMetaClass | str):
        db_name = None
        if isinstance(target, BaseQuery):
            db_name = target.expressions.get('db_name')
            tablename = target.expressions.get('table')
            if not tablename:
                tablename = utils.tablename(target.model)
        elif isinstance(target, ModelMetaClass):
            tablename = utils.tablename(target)
        else:
            tablename = target
        tablename = bash_wrap(tablename)
        if db_name:
            return f'{bash_wrap(db_name)}.{tablename}'
        return tablename

    def expr_where(self, query: BaseQuery):
        parts = []
        f = query.expressions.get('filter')
        if f:
            parts.append('WHERE')
            parts.append(self.expr_filter(f))
            return ' '.join(parts)
        else:
            return ''

    def expr_join(self, join: Join):
        pass

    def expr(self, exp: SqlBase):
        if isinstance(exp, ModelMetaClass):
            return self.expr_tablename(exp)
        elif isinstance(exp, BaseField):
            return self.expr_field(exp)
        elif isinstance(exp, BaseFilter):
            return self.expr_filter(exp)
        elif isinstance(exp, BaseFunc):
            return self.expr_func(exp)
        elif isinstance(exp, Query):
            return self.sql_query(exp)
        elif isinstance(exp, SqlValue):
            return self.expr_value(exp.value)
        elif isinstance(exp, Join):
            return self.expr_join(exp)
        else:
            return self.expr_value(exp)

    def expr_filter(self, f: BaseFilter):
        if isinstance(f, Expr):
            return f.expr
        elif isinstance(f, IsNull):
            left = self.expr(f.left)
            right = f.right.value if isinstance(f.right, SqlValue) else f.right
            if right is True:
                return f'{left} IS NULL'
            else:
                return f'{left} IS NOT NULL'
        elif isinstance(f, _Filter):
            left = self.expr(f.left)
            right = self.expr(f.right)
            return f'{left} {f.token} {right}'
        elif isinstance(f, And):
            expr_list = []
            for item in f.filters:
                expr_list.append(self.expr_filter(item))
            return ' AND '.join(expr_list)
        elif isinstance(f, Or):
            expr_list = []
            for item in f.filters:
                expr_list.append(self.expr_filter(item))
            return ' OR '.join(expr_list)
        raise OrmError('invalid filter')

    def __join_fields(self, fields: t.Union[BaseField, str]):
        parts = []
        for f in fields:
            if isinstance(f, BaseField):
                parts.append(self.expr_field(f))
            else:
                parts.append(f)
        return ', '.join(parts)

    def sql_create_table(self, model) -> str:
        sql_parts = [f'CREATE TABLE IF NOT EXISTS {utils.tablename(model)} (']
        fields = utils.model_fields(model)
        fields_expr = []
        for field in fields:
            if isinstance(field, (ForeignKey, Many, One)):
                continue
            field_parts = [f'`{field.db_column}`', self.field_db_type(field)]
            if not field.nullable:
                field_parts.append('NOT NULL')
            if field.auto_increment:
                field_parts.append('AUTO_INCREMENT')
            db_default = field.db_default
            if db_default is not None:
                field_parts.append(f"DEFAULT {db_default}")
            elif field.nullable:
                field_parts.append('DEFAULT NULL')
            table_field = ' '.join(field_parts)
            fields_expr.append(table_field)
        pks = model.get_primary_keys()
        if pks:
            pk_expr = ','.join([f"`{pk.db_column}`" for pk in pks])
            fields_expr.append(f'PRIMARY KEY ({pk_expr}) USING BTREE')
        sql_parts.append(',\n'.join(fields_expr))
        engine = self.config.get('engine', 'InnoDB')
        charset = self.config.get('charset', 'utf8mb4')
        sql_parts.append(f') ENGINE={engine} DEFAULT CHARSET={charset};')
        sql = '\n'.join(sql_parts)
        return sql

    def sql_alter_table_comment(self, model: ModelMetaClass) -> str:
        comment = inspect.getdoc(model)
        if comment:
            comment = comment.strip().split('\n')[0]
        sql = f"ALTER TABLE {self.expr_tablename(model)} COMMENT '{comment}';"
        return sql

    def sql_add_column(self, field: BaseField) -> str:
        if isinstance(field, (ForeignKey, Many, One)):
            return ''
        return self.__sql_column(field, 'ADD')

    def sql_alter_column(self, field: BaseField) -> str:
        return self.__sql_column(field, 'CHANGE')

    def __sql_column(self, field: BaseField, op='CHANGE') -> str:
        table_expr = self.expr_tablename(field.model)
        field_name = field.db_column
        parts = [
            f'ALTER TABLE {table_expr} {op} COLUMN `{field_name}`',
            f'`{field_name}`' if op == 'CHANGE' else '',
            self.field_db_type(field)
        ]
        if not field.nullable:
            parts.append('NOT NULL')
        else:
            parts.append('NULL')
        db_default = self.expr_field_db_default(field)
        default_value = field.default_value()
        if db_default:
            parts.append(f'DEFAULT {db_default}')
        elif default_value is not None:
            if default_value is True:
                default_value = 1
            elif default_value is False:
                default_value = 0
            parts.append(f"DEFAULT '{default_value}'")
        if field.auto_increment:
            parts.append('AUTO_INCREMENT')
        if field.comment:
            parts.append(f"COMMENT '{field.comment}'")
        if field.collate:
            parts.append('COLLATE')
            parts.append(f"'{field.collate}'")
        sql_list = [' '.join(parts) + ';']
        if field.unique:
            sql_list.append(f'ALTER TABLE {table_expr} ADD UNIQUE INDEX `{field_name}` (`{field_name}`);')
        if field.index:
            sql_list.append(f'ALTER TABLE {table_expr} ADD INDEX `{field_name}` (`{field_name}`);')
        return '\n'.join(sql_list)


def bash_wrap(value: str) -> str:
    if not value:
        return value
    if not value.startswith('`'):
        value = '`' + value
    if not value.endswith('`'):
        value = value + '`'
    return value
