# coding:utf-8

import asyncio

from makit.orm.tests.models import User


async def delete_test():
    async with db_demo.transaction() as session:
        await session.query(User).delete()
        await session.query(User).where(User.is_superuser == False).delete()


async def update_test():
    async with db_demo.transaction() as session:
        await session.query(User).delete()
        await session.query(User).where(User.is_superuser == False).update(name='changed')


async def save_test():
    async with db_demo.transaction() as session:
        # user = await session.query(User).where(User.username == 'admin').first()
        # user.name = 'changed'
        # await session.save(user)
        sql = "SELECT * FROM `information_schema`.`TABLES` WHERE `TABLE_SCHEMA`='aiguide' AND `TABLE_NAME`='chat_agent'"
        result = await session.exec_sql(sql)
        pass


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(save_test())
