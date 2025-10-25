# Copyright 2022 J.P. Morgan Chase & Co.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import datetime
import decimal
import re
import uuid
from typing import Annotated, Any, Dict, List, Union

import pytest

import py_avro_schema as pas
from py_avro_schema._testing import assert_schema


def test_date():
    py_type = datetime.date
    expected = {
        "type": "int",
        "logicalType": "date",
    }
    assert_schema(py_type, expected)


def test_date_annotated():
    py_type = Annotated[datetime.date, ...]
    expected = {
        "type": "int",
        "logicalType": "date",
    }
    assert_schema(py_type, expected)


def test_time():
    py_type = datetime.time
    expected = {
        "type": "long",
        "logicalType": "time-micros",
    }
    assert_schema(py_type, expected)


def test_time_annotated():
    py_type = Annotated[datetime.time, ...]
    expected = {
        "type": "long",
        "logicalType": "time-micros",
    }
    assert_schema(py_type, expected)


def test_time_milliseconds():
    py_type = datetime.time
    expected = {
        "type": "int",
        "logicalType": "time-millis",
    }
    options = pas.Option.MILLISECONDS
    assert_schema(py_type, expected, options=options)


def test_datetime():
    py_type = datetime.datetime
    expected = {
        "type": "long",
        "logicalType": "timestamp-micros",
    }
    assert_schema(py_type, expected)


def test_datetime_annotated():
    py_type = Annotated[datetime.datetime, ...]
    expected = {
        "type": "long",
        "logicalType": "timestamp-micros",
    }
    assert_schema(py_type, expected)


def test_datetime_milliseconds():
    py_type = datetime.datetime
    expected = {
        "type": "long",
        "logicalType": "timestamp-millis",
    }
    options = pas.Option.MILLISECONDS
    assert_schema(py_type, expected, options=options)


def test_timedelta():
    py_type = datetime.timedelta
    expected = {
        "type": "fixed",
        "name": "datetime.timedelta",
        "size": 12,
        "logicalType": "duration",
    }
    assert_schema(py_type, expected)


def test_timedelta_annotated():
    py_type = Annotated[datetime.timedelta, ...]
    expected = {
        "type": "fixed",
        "name": "datetime.timedelta",
        "size": 12,
        "logicalType": "duration",
    }
    assert_schema(py_type, expected)


def test_decimal():
    # Deprecated custom type hint for decimals
    py_type = pas.DecimalType[5, 2]
    expected = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
        "scale": 2,
    }
    assert_schema(py_type, expected)


def test_annotated_decimal():
    py_type = Annotated[decimal.Decimal, pas.DecimalMeta(precision=5, scale=2)]
    expected = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
        "scale": 2,
    }
    assert_schema(py_type, expected)


def test_annotated_decimal_default_scale():
    py_type = Annotated[decimal.Decimal, pas.DecimalMeta(precision=5)]
    expected = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
    }
    assert_schema(py_type, expected)


def test_annotated_decimal_additional_meta():
    py_type = Annotated[decimal.Decimal, "something else", pas.DecimalMeta(precision=5, scale=2)]
    expected = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
        "scale": 2,
    }
    assert_schema(py_type, expected)


def test_annotated_decimal_in_union():
    py_type = Union[Annotated[decimal.Decimal, pas.DecimalMeta(precision=5, scale=2)], None]
    expected = [
        {
            "type": "bytes",
            "logicalType": "decimal",
            "precision": 5,
            "scale": 2,
        },
        "null",
    ]
    assert_schema(py_type, expected)


def test_annotated_decimal_no_meta():
    py_type = Annotated[decimal.Decimal, ...]
    with pytest.raises(
        TypeError,
        match=re.escape(
            "typing.Annotated[decimal.Decimal, Ellipsis] is not annotated with a single 'py_avro_schema.DecimalMeta' "
            "object"
        ),
    ):
        assert_schema(py_type, {})


def test_annotated_decimal_2_meta():
    py_type = Annotated[decimal.Decimal, pas.DecimalMeta(precision=5, scale=2), pas.DecimalMeta(precision=4)]
    with pytest.raises(
        TypeError,
        match=re.escape(
            "typing.Annotated[decimal.Decimal, DecimalMeta(precision=5, scale=2), DecimalMeta(precision=4, scale=None)]"
            " is not annotated with a single 'py_avro_schema.DecimalMeta' object"
        ),
    ):
        assert_schema(py_type, {})


def test_annotated_decimal_tuple():
    py_type = Annotated[decimal.Decimal, (5, 2)]
    with pytest.raises(
        TypeError,
        match=re.escape(
            "typing.Annotated[decimal.Decimal, (5, 2)] is not annotated with a single 'py_avro_schema.DecimalMeta' "
            "object"
        ),
    ):
        assert_schema(py_type, {})


def test_multiple_decimals():
    # Test the magic with _GenericAlias!
    py_type_1 = pas.DecimalType[5, 2]
    expected_1 = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 5,
        "scale": 2,
    }
    py_type_2 = pas.DecimalType[3, 1]
    expected_2 = {
        "type": "bytes",
        "logicalType": "decimal",
        "precision": 3,
        "scale": 1,
    }
    assert_schema(py_type_1, expected_1)
    assert_schema(py_type_2, expected_2)


def test_uuid():
    py_type = uuid.UUID
    expected = {
        "type": "string",
        "logicalType": "uuid",
    }
    assert_schema(py_type, expected)


def test_uuid_annotated():
    py_type = Annotated[uuid.UUID, ...]
    expected = {
        "type": "string",
        "logicalType": "uuid",
    }
    assert_schema(py_type, expected)


def test_dict_json_logical_string_field():
    py_type = Dict[str, Any]
    expected = {
        "type": "string",
        "logicalType": "json",
    }
    options = pas.Option.LOGICAL_JSON_STRING
    assert_schema(py_type, expected, options=options)


def test_dict_json_logical_bytes_field():
    py_type = Dict[str, Any]
    expected = {
        "type": "bytes",
        "logicalType": "json",
    }
    assert_schema(py_type, expected)


def test_list_json_logical_string_field():
    py_type = List[Dict[str, Any]]
    expected = {
        "type": "string",
        "logicalType": "json",
    }
    options = pas.Option.LOGICAL_JSON_STRING
    assert_schema(py_type, expected, options=options)


def test_list_json_logical_bytes_field():
    py_type = List[Dict[str, Any]]
    expected = {
        "type": "bytes",
        "logicalType": "json",
    }
    assert_schema(py_type, expected)
