# coding:utf-8

import asyncio
import re
from asyncio import AbstractEventLoop
from functools import cached_property

from logzero import setup_logger

from makit.orm import utils
from makit.orm.base import BaseExecutor, ModelMetaClass
from makit.orm.db.mysql import MysqlClient, MysqlExecutor
from makit.orm.errors import OrmError
from makit.orm.fields import Relation
from makit.orm.filters import Equal
from makit.orm.model import DbModel
from makit.orm.query import Query


class DB:

    def __init__(self, connstr: str, logger=None, **kwargs):
        self._connstr = connstr
        self.logger = logger or setup_logger()
        self.loop = kwargs.pop('loop', asyncio.get_event_loop())
        self.config = kwargs
        self.__parse_connstr(connstr)

    def __parse_connstr(self, connstr):
        regex = re.compile(r'(?P<dbtype>\w+)://(?P<user>\w+):(?P<pwd>.+?)@'
                           r'(?P<host>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(?P<port>\d+)/'
                           r'(?P<db>\w+)\??'
                           r'(?P<param_str>([a-z0-9_]+=[a-zA-Z0-9_]+&?)*)')
        matches = regex.match(connstr)
        data = matches.groupdict()
        port = data.get('port')
        data['port'] = int(port)
        param_str = data.pop('param_str', None)
        if param_str:
            parts = param_str.split('&')
            for part in parts:
                k, v = part.split('=')
                data[k] = v
        self.config.update(data)

    @cached_property
    def debug(self):
        return self.client.debug

    @cached_property
    def db_type(self):
        return self.config.get('dbtype')

    @cached_property
    def db_name(self):
        return self.config.get('db')

    @cached_property
    def client(self):
        dbtype = self.config.get('dbtype')
        if dbtype == 'mysql':
            client = MysqlClient(self.config, logger=self.logger, loop=self.loop)
            return client
        else:
            raise OrmError(f'Unsupported db: {dbtype}')

    async def session(self):
        conn = await self.client.get_connection()
        cursor = await conn.cursor()
        if self.db_type == 'mysql':
            executor = MysqlExecutor(conn, cursor, logger=self.logger)
            await executor.auto_commit()
        else:
            raise OrmError(f'Unknown db type: {self.db_type}')
        return DbSession(executor=executor, db=self)

    def transaction(self):
        tran = Transaction(self)
        tran.client = self.client
        return tran


class DbSession:
    def __init__(self, db, executor: BaseExecutor):
        self.db = db
        self.executor = executor
        self.executor.client = db.client

    @property
    def loop(self) -> AbstractEventLoop:
        return self.db.loop

    @property
    def closed(self):
        return self.executor.is_closed()

    async def begin(self):
        await self.executor.begin()

    async def rollback(self):
        await self.executor.rollback()

    async def commit(self):
        await self.executor.commit()

    async def close(self):
        await self.executor.close()

    async def create(self, *instances: DbModel):
        queries = dict()
        for instance in instances:
            classname = instance.__class__.__name__
            if classname not in queries:
                queries[classname] = self(instance.__class__).create(instance)
                continue
            query = queries[classname]
            query.create(instance)
        for classname, query in queries.items():
            await query

    async def save(self, instance: DbModel):
        cls = instance.__class__
        pk_filters = []
        pks = cls.get_meta().primary_keys
        for pk in pks:
            pk_value = getattr(instance, pk.name)
            pk_filters.append(Equal(pk, pk_value))
        if not pk_filters:
            await self.create(instance)
            return
        query = self(cls).where(*pk_filters)
        exists = await query.exists()
        if exists:
            # 更新数据
            fields = utils.model_fields(cls)
            data = dict()
            for f in fields:
                if f.pk or isinstance(f, Relation):
                    continue
                value = getattr(instance, f.name)
                data[f.db_column] = value
            await query.update(**data)
        else:
            await self.create(instance)

    async def exec_sql(self, sql: str, *args):
        return await self.executor.exec_sql(sql, *args)

    def __call__(self, model: ModelMetaClass | str):
        return Query(model=model, executor=self.executor)

    def __del__(self):
        if not self.closed:
            async def cleanup():
                if self.executor.in_transaction:
                    await self.executor.commit()
                await self.close()

            self.loop.create_task(cleanup())


class Transaction:
    def __init__(self, db):
        self.db = db
        self.client = None

    async def __aenter__(self):
        conn = await self.client.get_connection()
        cursor = await conn.cursor()
        await conn.begin()
        executor = MysqlExecutor(conn, cursor, logger=self.client.logger)
        self.session = session = DbSession(self.db, executor)
        return session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_tb:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()
        except Exception as e:
            await self.session.rollback()
            await self.session.close()
            raise e


def connect(connstr: str, **kwargs) -> DB:
    return DB(connstr, **kwargs)
