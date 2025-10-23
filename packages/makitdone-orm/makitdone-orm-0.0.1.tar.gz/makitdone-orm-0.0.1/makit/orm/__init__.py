# coding:utf-8

from makit.orm.base import BaseField, Expr
from makit.orm.connection import DB
from makit.orm.fields import (
    String, BigInt, Boolean, Float, Int, UUID, SmallInt, TinyInt, Text, Json,
    DateTime, Date, Time, Timestamp,
    Blob, Binary, Image, File,
    ForeignKey, Many
)
from makit.orm.model import DbModel

__all__ = [
    Expr,
    DB,
    DbModel,
    BaseField,
    String,
    UUID,
    BigInt,
    Int,
    SmallInt,
    TinyInt,
    Float,
    Boolean,
    Text,
    Json,
    DateTime,
    Date,
    Time,
    Timestamp,
    Blob,
    Binary,
    Image,
    File,
    ForeignKey,
    Many
]


def expr(s: str, *args):
    """
    SQL表达式

    示例：

    1. expr('YEAR(`user`.joined_at)')
    2. expr('YEAR(`user`.joined_at IN %s)', [2024, 2025])
    """
    return Expr(s, *args)
