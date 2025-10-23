# coding:utf-8


import asyncio

from makit.orm.connection import connect
from makit.orm.tests.models import User, connstr


async def preload_test(session):
    user = await session.query(User).where(User.id == 1).preload(User.org).first()
    pass


async def init_data():
    db_demo = connect(connstr, loop=loop)
    async with db_demo.transaction() as session:
        await preload_test(session)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_data())
