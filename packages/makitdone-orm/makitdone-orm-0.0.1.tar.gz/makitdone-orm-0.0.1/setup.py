from setuptools import setup

setup(
    name='makitdone-orm',
    version='0.0.1',
    packages=[
        'makit.orm',
        'makit.orm.db',
        'makit.orm.tests'
    ],
    namespace_package=['makit', 'makit.orm'],
    install_requires=[
        'setuptools',
        'makitdone-lib~=2.0.0',
        'PyMySQL~=1.1.2',
        'aiomysql~=0.3.2',
        'logzero~=1.7.0'
    ],
    python_requires='>=3.11',
    url='https://gitee.com/makitdone/makitdone-orm',
    license='MIT',
    author='liangchao',
    author_email='liang20201101@163.com',
    description='orm框架，目前仅支持mysql'
)
