import datetime
import ipaddress
import unittest
import uuid
from typing import Literal, Optional, Union

from strong_typing.core import JsonType
from strong_typing.exception import JsonKeyError, JsonTypeError, JsonValueError
from strong_typing.serialization import json_to_generic, json_to_object, object_to_json

from .sample_types import (
    UID,
    BinaryValueWrapper,
    ClassA,
    ClassB,
    ClassC,
    FrozenValueWrapper,
    LiteralWrapper,
    NestedDataclass,
    NestedGenericType,
    NestedJson,
    OptionalValueWrapper,
    Side,
    SimpleDataclass,
    SimpleDerivedClass,
    SimpleValueWrapper,
    Suit,
)


def test_function() -> None:
    pass


async def test_async_function() -> None:
    pass


class TestDeserialization(unittest.TestCase):
    def test_deserialization_simple(self) -> None:
        self.assertEqual(json_to_object(type(None), None), None)
        self.assertEqual(json_to_object(bool, True), True)
        self.assertEqual(json_to_object(int, 23), 23)
        self.assertEqual(json_to_object(float, 4.5), 4.5)
        self.assertEqual(json_to_object(str, "an"), "an")
        self.assertEqual(json_to_object(bytes, "QU4="), bytes([65, 78]))
        self.assertEqual(json_to_object(Side, "L"), Side.LEFT)
        self.assertEqual(json_to_object(Suit, 1), Suit.Diamonds)
        self.assertEqual(
            json_to_object(uuid.UUID, "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"),
            uuid.UUID("f81d4fae-7dec-11d0-a765-00a0c91e6bf6"),
        )
        self.assertEqual(
            json_to_object(ipaddress.IPv4Address, "192.0.2.1"),
            ipaddress.IPv4Address("192.0.2.1"),
        )
        self.assertEqual(
            json_to_object(ipaddress.IPv6Address, "2001:DB8:0:0:8:800:200C:417A"),
            ipaddress.IPv6Address("2001:DB8:0:0:8:800:200C:417A"),
        )

        with self.assertRaises(JsonTypeError):
            json_to_object(type(None), 23)
        with self.assertRaises(JsonTypeError):
            json_to_object(int, None)
        with self.assertRaises(JsonTypeError):
            json_to_object(int, "int")
        with self.assertRaises(JsonTypeError):
            json_to_object(str, None)
        with self.assertRaises(JsonTypeError):
            json_to_object(str, 1982)

    def test_deserialization_datetime(self) -> None:
        self.assertEqual(
            json_to_object(datetime.datetime, "1989-10-23T01:45:50Z"),
            datetime.datetime(1989, 10, 23, 1, 45, 50, tzinfo=datetime.timezone.utc),
        )
        timezone_cet = datetime.timezone(datetime.timedelta(seconds=3600))
        self.assertEqual(
            json_to_object(datetime.datetime, "1989-10-23T01:45:50+01:00"),
            datetime.datetime(1989, 10, 23, 1, 45, 50, tzinfo=timezone_cet),
        )
        with self.assertRaises(JsonValueError):
            json_to_object(datetime.datetime, "1989-10-23T01:45:50")

    def test_deserialization_timedelta(self) -> None:
        self.assertEqual(json_to_object(datetime.timedelta, "P0D"), datetime.timedelta())
        self.assertEqual(json_to_object(datetime.timedelta, "PT0S"), datetime.timedelta())
        self.assertEqual(json_to_object(datetime.timedelta, "P2W"), datetime.timedelta(days=14))
        self.assertEqual(json_to_object(datetime.timedelta, "P365D"), datetime.timedelta(days=365))
        self.assertEqual(json_to_object(datetime.timedelta, "P1W3D"), datetime.timedelta(days=10))
        self.assertEqual(json_to_object(datetime.timedelta, "PT23H"), datetime.timedelta(hours=23))
        self.assertEqual(json_to_object(datetime.timedelta, "PT23H0M0S"), datetime.timedelta(hours=23))
        self.assertEqual(json_to_object(datetime.timedelta, "PT59M"), datetime.timedelta(minutes=59))
        self.assertEqual(json_to_object(datetime.timedelta, "PT59M0S"), datetime.timedelta(minutes=59))
        self.assertEqual(
            json_to_object(datetime.timedelta, "PT59.5S"), datetime.timedelta(seconds=59, milliseconds=500)
        )
        self.assertEqual(
            json_to_object(datetime.timedelta, "PT59.123S"), datetime.timedelta(seconds=59, milliseconds=123)
        )
        self.assertEqual(
            json_to_object(datetime.timedelta, "PT59.000123S"), datetime.timedelta(seconds=59, microseconds=123)
        )
        self.assertEqual(json_to_object(datetime.timedelta, "P365DT59S"), datetime.timedelta(days=365, seconds=59))
        self.assertEqual(
            json_to_object(datetime.timedelta, "P365DT23H39M59S"),
            datetime.timedelta(days=365, hours=23, minutes=39, seconds=59),
        )
        with self.assertRaises(JsonValueError):
            json_to_object(datetime.timedelta, "PT59.000000001S")
        with self.assertRaises(JsonValueError):
            json_to_object(datetime.timedelta, "P1Y")
        with self.assertRaises(JsonValueError):
            json_to_object(datetime.timedelta, "P1M")

    def test_deserialization_class(self) -> None:
        self.assertEqual(json_to_object(SimpleValueWrapper, {"value": 42}), SimpleValueWrapper(42))
        self.assertEqual(
            json_to_object(FrozenValueWrapper, {"value": 42}),
            FrozenValueWrapper(42),
        )

    def test_deserialization_composite(self) -> None:
        self.assertEqual(json_to_object(UID, "1.2.3.4567.8900"), UID("1.2.3.4567.8900"))
        self.assertEqual(
            json_to_object(BinaryValueWrapper, {"value": "QU4="}),
            BinaryValueWrapper(bytes([65, 78])),
        )

    def test_deserialization_collection(self) -> None:
        self.assertEqual(json_to_object(list[int], [1, 2, 3]), [1, 2, 3])
        self.assertEqual(
            json_to_object(dict[str, int], {"a": 1, "b": 2, "c": 3}),
            {"a": 1, "b": 2, "c": 3},
        )
        self.assertEqual(json_to_object(set[int], [1, 2, 3]), set([1, 2, 3]))

        with self.assertRaises(JsonTypeError):
            json_to_object(list[int], 23)
        with self.assertRaises(JsonTypeError):
            json_to_object(dict[str, int], "string")
        with self.assertRaises(JsonTypeError):
            json_to_object(set[int], 42)

        with self.assertRaises(TypeError):
            json_to_object(list, [1, 2, 3])
        with self.assertRaises(TypeError):
            json_to_object(dict, {"key": 42})
        with self.assertRaises(TypeError):
            json_to_object(set, [1, 2, 3])
        with self.assertRaises(TypeError):
            json_to_object(tuple, [1, "two"])

    def test_deserialization_optional(self) -> None:
        self.assertEqual(json_to_generic(Optional[int], None), None)
        self.assertEqual(json_to_generic(Optional[int], 42), 42)

        self.assertEqual(
            json_to_object(OptionalValueWrapper, {}),
            OptionalValueWrapper(None),
        )
        self.assertEqual(
            json_to_object(OptionalValueWrapper, {"value": 42}),
            OptionalValueWrapper(42),
        )

        with self.assertRaises(JsonKeyError):
            json_to_object(OptionalValueWrapper, {"value": 23, "extra": 42})

    def test_deserialization_literal(self) -> None:
        self.assertEqual(json_to_generic(Literal["val1", "val2", "val3"], "val1"), "val1")
        self.assertEqual(json_to_generic(Literal["val1", "val2", "val3"], "val3"), "val3")
        self.assertEqual(json_to_generic(Literal[1, 2, 3], 1), 1)
        self.assertEqual(json_to_generic(Literal[1, 2, 3], 3), 3)

        self.assertEqual(json_to_object(LiteralWrapper, {"value": "val1"}), LiteralWrapper("val1"))
        self.assertEqual(json_to_object(LiteralWrapper, {"value": "val2"}), LiteralWrapper("val2"))
        self.assertEqual(json_to_object(LiteralWrapper, {"value": "val3"}), LiteralWrapper("val3"))

        with self.assertRaises(TypeError):
            json_to_generic(Literal["value", 1], "value")
        with self.assertRaises(TypeError):
            json_to_generic(Literal[1, "value"], "value")
        with self.assertRaises(JsonTypeError):
            json_to_generic(Literal["val1", "val2", "val3"], "value")

    def test_deserialization_generic(self) -> None:
        self.assertEqual(
            json_to_object(
                NestedGenericType,
                {"list_of_str": ["str"], "list_of_dict": [{"key": "value"}]},
            ),
            NestedGenericType(list_of_str=["str"], list_of_dict=[{"key": "value"}]),
        )

    def test_deserialization_union(self) -> None:
        # built-in types
        self.assertEqual(json_to_generic(Union[int, str], 42), 42)
        self.assertEqual(json_to_generic(Union[int, str], "a string"), "a string")
        self.assertEqual(json_to_generic(Union[str, int], 42), 42)
        self.assertEqual(json_to_generic(Union[str, int], "a string"), "a string")
        with self.assertRaises(JsonKeyError):
            json_to_generic(Union[int, str], 10.23)

        # mixed (built-in and user-defined) types
        self.assertEqual(json_to_generic(Union[SimpleValueWrapper, int], 42), 42)
        self.assertEqual(json_to_generic(Union[int, SimpleValueWrapper], 42), 42)
        self.assertEqual(
            json_to_generic(Union[int, SimpleValueWrapper], {"value": 42}),
            SimpleValueWrapper(42),
        )
        self.assertEqual(
            json_to_generic(Union[SimpleValueWrapper, int], {"value": 42}),
            SimpleValueWrapper(42),
        )

        # class types with disjoint field names
        self.assertEqual(
            json_to_generic(Union[SimpleDataclass, SimpleValueWrapper], {"value": 42}),
            SimpleValueWrapper(42),
        )
        self.assertEqual(
            json_to_generic(Union[SimpleDataclass, SimpleValueWrapper], {"int_value": 42}),
            SimpleDataclass(int_value=42),
        )

        # class types with overlapping field names
        self.assertEqual(
            json_to_generic(
                Union[SimpleDerivedClass, SimpleDataclass],
                {"extra_str_value": "twenty-o-four"},
            ),
            SimpleDerivedClass(extra_str_value="twenty-o-four"),
        )
        self.assertEqual(
            json_to_generic(
                Union[SimpleDataclass, SimpleDerivedClass],
                {"extra_str_value": "twenty-o-four"},
            ),
            SimpleDerivedClass(extra_str_value="twenty-o-four"),
        )
        self.assertEqual(
            json_to_generic(
                Union[SimpleDataclass, SimpleDerivedClass],
                {"int_value": 2004},
            ),
            SimpleDataclass(int_value=2004),
        )

        # class types with literal-based disambiguation
        self.assertEqual(
            json_to_generic(
                Union[ClassA, ClassB, ClassC],
                {"type": "A", "name": "A", "value": "string"},
            ),
            ClassA(name="A", type="A", value="string"),
        )
        self.assertEqual(
            json_to_generic(
                Union[ClassA, ClassB, ClassC],
                {"type": "B", "name": "B", "value": "string"},
            ),
            ClassB(name="B", type="B", value="string"),
        )
        self.assertEqual(
            json_to_generic(
                Union[ClassA, ClassB, ClassC],
                {"type": "A", "name": "a", "value": "string"},
            ),
            ClassA(name="a", type="A", value="string"),
        )
        self.assertEqual(
            json_to_generic(
                Union[ClassA, ClassB, ClassC],
                {"type": "B", "name": "b", "value": "string"},
            ),
            ClassB(name="b", type="B", value="string"),
        )

    def test_deserialization_recursive(self) -> None:
        self.assertEqual(json_to_object(NestedJson, {"json": []}), NestedJson([]))
        self.assertEqual(json_to_object(NestedJson, {"json": {}}), NestedJson({}))
        self.assertEqual(
            json_to_object(NestedJson, {"json": [{"key1": "value1"}, {"key2": "value2"}]}),
            NestedJson([{"key1": "value1"}, {"key2": "value2"}]),
        )

    def test_deserialization_json(self) -> None:
        self.assertEqual(json_to_generic(JsonType, True), True)
        self.assertEqual(json_to_generic(JsonType, 23), 23)
        self.assertEqual(json_to_generic(JsonType, "string"), "string")
        self.assertEqual(json_to_generic(JsonType, []), [])
        self.assertEqual(json_to_generic(JsonType, [1, 2, 3]), [1, 2, 3])
        self.assertEqual(json_to_generic(JsonType, [{}, {}]), [{}, {}])
        self.assertEqual(json_to_generic(JsonType, {"key": "value"}), {"key": "value"})

    def test_object_deserialization(self) -> None:
        """Test composition and inheritance with object de-serialization."""

        json_dict = object_to_json(NestedDataclass())
        obj = json_to_object(NestedDataclass, json_dict)
        self.assertEqual(obj, NestedDataclass())


if __name__ == "__main__":
    unittest.main()
