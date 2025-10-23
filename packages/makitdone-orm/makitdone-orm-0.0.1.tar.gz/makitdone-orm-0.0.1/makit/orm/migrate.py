# coding:utf-8

from makit.orm import utils
from makit.orm.base import ModelMetaClass, BaseField, MetaInfo
from makit.orm.connection import DbSession
from makit.orm.fields import ForeignKey


class Migration:
    def __init__(self, session: DbSession):
        self.session = session
        self.sql_builder = session.executor.sql_builder

    async def migrate(self, models=None):
        executor = self.session.executor
        tables = await executor.get_db_tables()
        if not models:
            models = ModelMetaClass.all
        fk_list = []
        for model in models:
            meta_info: MetaInfo = getattr(model, '_meta')
            if meta_info.abstract:
                continue
            tablename = utils.tablename(model)
            if tablename not in tables:
                await self.create_table(model)
            await self.alter_table_comment(model)
            await self.drop_constraints(model=model)
            fields = utils.model_fields(model)
            for field in fields:
                if isinstance(field, ForeignKey):
                    fk_list.append(field)
                    field = field.field
                exists = await executor.field_exists(field)
                if not exists:
                    await self.add_column(field)
                else:
                    await self.alter_column(field)
        for fk in fk_list:
            await self.add_constraint(fk)

    async def create_table(self, model: ModelMetaClass):
        sql = self.sql_builder.sql_create_table(model)
        await self.session.exec_sql(sql)

    async def alter_table_comment(self, model: ModelMetaClass):
        sql = self.sql_builder.sql_alter_table_comment(model)
        await self.session.exec_sql(sql)

    async def add_column(self, field: BaseField):
        sql = self.sql_builder.sql_add_column(field)
        if sql:
            await self.session.exec_sql(sql)

    async def alter_column(self, field: BaseField):
        sql = self.sql_builder.sql_alter_column(field)
        if sql:
            await self.session.exec_sql(sql)

    async def drop_constraints(self, model: ModelMetaClass = None):
        await self.session.executor.drop_constraints(model)

    async def add_constraint(self, field: BaseField):
        sql = self.sql_builder.sql_add_fk_constraint(field)
        await self.session.exec_sql(sql)
