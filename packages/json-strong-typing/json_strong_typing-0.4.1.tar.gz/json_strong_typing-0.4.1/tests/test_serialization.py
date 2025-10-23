import datetime
import ipaddress
import typing
import unittest
import uuid

from strong_typing.core import JsonType
from strong_typing.exception import JsonValueError
from strong_typing.schema import validate_object
from strong_typing.serialization import object_to_json

from .sample_types import (
    UID,
    AnnotatedSimpleDataclass,
    BinaryValueWrapper,
    CompositeDataclass,
    FrozenValueWrapper,
    LiteralWrapper,
    MultipleInheritanceDerivedClass,
    NestedDataclass,
    NestedJson,
    Side,
    SimpleDataclass,
    SimpleTypedClass,
    SimpleTypedNamedTuple,
    SimpleUntypedClass,
    SimpleUntypedNamedTuple,
    SimpleValueWrapper,
    Suit,
)


def test_function() -> None:
    pass


async def test_async_function() -> None:
    pass


class TestSerialization(unittest.TestCase):
    def test_composite_object(self) -> None:
        json_dict = object_to_json(SimpleDataclass())
        validate_object(SimpleDataclass, json_dict)

        json_dict = object_to_json(AnnotatedSimpleDataclass())
        validate_object(AnnotatedSimpleDataclass, json_dict)

        json_dict = object_to_json(CompositeDataclass())
        validate_object(CompositeDataclass, json_dict)

        json_dict = object_to_json(NestedDataclass())
        validate_object(NestedDataclass, json_dict)

    def test_serialization_simple(self) -> None:
        self.assertEqual(object_to_json(None), None)
        self.assertEqual(object_to_json(True), True)
        self.assertEqual(object_to_json(23), 23)
        self.assertEqual(object_to_json(4.5), 4.5)
        self.assertEqual(object_to_json("an"), "an")
        self.assertEqual(object_to_json(bytes([65, 78])), "QU4=")
        self.assertEqual(object_to_json(Side.LEFT), "L")
        self.assertEqual(object_to_json(Suit.Diamonds), 1)
        self.assertEqual(
            object_to_json(uuid.UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6")),
            "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
        )
        self.assertEqual(
            object_to_json(ipaddress.IPv4Address("192.0.2.1")),
            "192.0.2.1",
        )
        self.assertEqual(
            object_to_json(ipaddress.IPv6Address("2001:DB8:0:0:8:800:200C:417A")),
            "2001:db8::8:800:200c:417a",
        )

    def test_serialization_datetime(self) -> None:
        self.assertEqual(
            object_to_json(datetime.datetime(1989, 10, 23, 1, 45, 50, tzinfo=datetime.timezone.utc)),
            "1989-10-23T01:45:50Z",
        )
        timezone_cet = datetime.timezone(datetime.timedelta(seconds=3600))
        self.assertEqual(
            object_to_json(datetime.datetime(1989, 10, 23, 1, 45, 50, tzinfo=timezone_cet)),
            "1989-10-23T01:45:50+01:00",
        )
        with self.assertRaises(JsonValueError):
            object_to_json(datetime.datetime(1989, 10, 23, 1, 45, 50))

    def test_serialization_timedelta(self) -> None:
        self.assertEqual(object_to_json(datetime.timedelta()), "PT0S")
        self.assertEqual(object_to_json(datetime.timedelta(days=365)), "P365D")
        self.assertEqual(object_to_json(datetime.timedelta(hours=23)), "PT23H0M0S")
        self.assertEqual(object_to_json(datetime.timedelta(minutes=59)), "PT59M0S")
        self.assertEqual(object_to_json(datetime.timedelta(seconds=59, milliseconds=500)), "PT59.500S")
        self.assertEqual(object_to_json(datetime.timedelta(seconds=59, milliseconds=123)), "PT59.123S")
        self.assertEqual(object_to_json(datetime.timedelta(seconds=59, microseconds=123)), "PT59.000123S")
        self.assertEqual(object_to_json(datetime.timedelta(days=365, seconds=59)), "P365DT59S")
        self.assertEqual(
            object_to_json(datetime.timedelta(days=365, hours=23, minutes=39, seconds=59)), "P365DT23H39M59S"
        )

    def test_serialization_literal(self) -> None:
        self.assertEqual(object_to_json(LiteralWrapper("val1")), {"value": "val1"})
        self.assertEqual(object_to_json(LiteralWrapper("val2")), {"value": "val2"})
        self.assertEqual(object_to_json(LiteralWrapper("val3")), {"value": "val3"})

    def test_serialization_namedtuple(self) -> None:
        self.assertEqual(
            object_to_json(SimpleTypedNamedTuple(42, "string")),
            {"int_value": 42, "str_value": "string"},
        )
        self.assertEqual(
            object_to_json(SimpleUntypedNamedTuple(42, "string")),
            {"int_value": 42, "str_value": "string"},
        )

    def test_serialization_class(self) -> None:
        self.assertEqual(object_to_json(SimpleValueWrapper(42)), {"value": 42})
        self.assertEqual(object_to_json(FrozenValueWrapper(42)), {"value": 42})
        self.assertEqual(
            object_to_json(SimpleTypedClass(42, "string")),
            {"int_value": 42, "str_value": "string"},
        )
        self.assertEqual(
            object_to_json(SimpleUntypedClass(42, "string")),
            {"int_value": 42, "str_value": "string"},
        )

    def test_serialization_collection(self) -> None:
        self.assertEqual(object_to_json([1, 2, 3]), [1, 2, 3])
        self.assertEqual(object_to_json({"a": 1, "b": 2, "c": 3}), {"a": 1, "b": 2, "c": 3})
        self.assertEqual(object_to_json(set([1, 2, 3])), [1, 2, 3])
        self.assertEqual(object_to_json(tuple([1, "two"])), [1, "two"])

    def test_serialization_composite(self) -> None:
        self.assertEqual(object_to_json(UID("1.2.3.4567.8900")), "1.2.3.4567.8900")
        self.assertEqual(object_to_json(BinaryValueWrapper(bytes([65, 78]))), {"value": "QU4="})

    def test_serialization_type_mismatch(self) -> None:
        self.assertRaises(TypeError, object_to_json, test_function)  # function
        self.assertRaises(TypeError, object_to_json, test_async_function)  # function
        self.assertRaises(TypeError, object_to_json, TestSerialization)  # class
        self.assertRaises(TypeError, object_to_json, self.test_serialization_type_mismatch)  # method

    def test_object_serialization(self) -> None:
        """Test composition and inheritance with object serialization."""

        json_dict = typing.cast(dict[str, JsonType], object_to_json(SimpleDataclass()))
        self.assertDictEqual(
            json_dict,
            {
                "bool_value": True,
                "int_value": 23,
                "float_value": 4.5,
                "str_value": "string",
                "date_value": "1970-01-01",
                "time_value": "06:15:30",
                "datetime_value": "1989-10-23T01:45:50Z",
                "duration_value": "P365DT2M4.000001S",
                "guid_value": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
            },
        )

        json_dict = typing.cast(
            dict[str, JsonType],
            object_to_json(
                CompositeDataclass(
                    list_value=["a", "b", "c"],
                    dict_value={"key": 42},
                    set_value=set(i for i in range(0, 4)),
                )
            ),
        )
        self.assertDictEqual(
            json_dict,
            {
                "list_value": ["a", "b", "c"],
                "dict_value": {"key": 42},
                "set_value": [0, 1, 2, 3],
                "tuple_value": [True, 2, "three"],
                "named_tuple_value": {"int_value": 1, "str_value": "second"},
            },
        )

        json_dict = typing.cast(dict[str, JsonType], object_to_json(MultipleInheritanceDerivedClass()))
        self.assertDictEqual(
            json_dict,
            {
                "bool_value": True,
                "int_value": 23,
                "float_value": 4.5,
                "str_value": "string",
                "date_value": "1970-01-01",
                "time_value": "06:15:30",
                "datetime_value": "1989-10-23T01:45:50Z",
                "duration_value": "P365DT2M4.000001S",
                "guid_value": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
                "list_value": [],
                "dict_value": {},
                "set_value": [],
                "tuple_value": [True, 2, "three"],
                "named_tuple_value": {"int_value": 1, "str_value": "second"},
                "extra_int_value": 0,
                "extra_str_value": "zero",
                "extra_optional_value": "value",
            },
        )

        json_dict = typing.cast(dict[str, JsonType], object_to_json(NestedDataclass()))
        self.assertDictEqual(
            json_dict,
            {
                "obj_value": {
                    "list_value": ["a", "b", "c"],
                    "dict_value": {"key": 42},
                    "set_value": [],
                    "tuple_value": [True, 2, "three"],
                    "named_tuple_value": {"int_value": 1, "str_value": "second"},
                },
                "list_value": [{"value": 1}, {"value": 2}],
                "dict_value": {
                    "a": {"value": 3},
                    "b": {"value": 4},
                    "c": {"value": 5},
                },
            },
        )

    def test_recursive_serialization(self) -> None:
        """Test object serialization with types that have a recursive definition, including forward references."""

        self.assertEqual(
            object_to_json(
                NestedJson(
                    {
                        "boolean": True,
                        "integer": 82,
                        "string": "value",
                        "array": [1, 2, 3],
                    }
                )
            ),
            {
                "json": {
                    "boolean": True,
                    "integer": 82,
                    "string": "value",
                    "array": [1, 2, 3],
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
