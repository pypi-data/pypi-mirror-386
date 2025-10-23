# coding:utf-8

import asyncio
from uuid import UUID

from makit.orm.connection import connect
from makit.orm.migrate import Migration
from makit.orm.tests.models import connstr, User, DailyReport


async def all_test(db):
    async with db.transaction() as session:
        mig = Migration(session)
        await mig.migrate()

        user = User(
            name='超级管理员',
            username='admin',
            is_superuser=True,
            password='ssss'
        )
        await session.create(user)

        user = await session.query(User).first()
        assert user.username == 'admin'

        user = await session.query(User).where(User.is_superuser == True).first()
        assert user.username == 'admin'

        user = await session.query(User).where(User.username == 'admin').first()
        assert user.name == '超级管理员'

        users = await session.query(User).where(User.is_superuser == False).all()
        assert len(users) == 0

        users = await session.query(User).select(User.username, User.is_superuser)
        assert len(users) == 1
        for user in users:
            assert user.name is None
            assert user.username == 'admin'

        count = await session.query(User).count()
        assert count == 1

        exists = await session.query(User).where(User.is_superuser == True).exists()
        assert exists is True

        exists = await session.query(User).where(User.is_superuser == False).exists()
        assert exists is False

        await session.query(User).get_or_create(
            defaults=dict(name='admin', ),
            username='admin',
        )
        user = await session.query(User).where(User.username == 'admin').first()
        assert user.name == '超级管理员'

        user.name = 'admin'
        await session.save(user)

        user = await session.query(User).where(User.username == 'admin').first()
        assert user.name == 'admin'

        await session.query(User).where(User.username == 'admin').update(name='超级管理员')

        user = await session.query(User).where(User.username == 'admin').first()
        assert user.name == '超级管理员'

        report = DailyReport(summary='This is my first report', user_id=user.id)
        await session.create(report)
        assert str(UUID(report.id)) == report.id

        await session.query(DailyReport).delete()

        await session.query(User).where(User.username == 'admin').delete()

        user = await session.query(User).where(User.username == 'admin').first()
        assert user is None

        # users = await session.query(User).value_list()
        # print(users)
        # users = await session.query(User).as_tuple()
        # print(users)
        #
        # users = await session.query(User).where(is_superuser=False)
        # print(users)


def test_main():
    loop = asyncio.get_event_loop()
    db = connect(connstr, loop=loop)
    loop.run_until_complete(all_test(db))
