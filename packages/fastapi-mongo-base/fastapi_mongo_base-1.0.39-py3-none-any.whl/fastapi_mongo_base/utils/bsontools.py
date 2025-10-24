import uuid
from decimal import Decimal

from bson import Binary
from bson.decimal128 import Decimal128


def decimal_amount(value: object) -> Decimal:
    if value is None:
        return value
    if isinstance(value, Decimal128):
        return Decimal(value.to_decimal())
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    return Decimal(value)


def get_bson_value(value: object) -> object:
    if isinstance(value, Decimal):
        return Decimal128(value)
    if isinstance(value, bytes):
        return Binary(value)
    if isinstance(value, uuid.UUID):
        return Binary.from_uuid(value)
    if isinstance(value, dict):
        return {k: get_bson_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [get_bson_value(v) for v in value]
    return value
