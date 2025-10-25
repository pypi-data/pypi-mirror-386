from datetime import date, time, datetime, timezone, timedelta

import re
import pytest
from json import dumps
from base64 import b64encode, b64decode
from dateutil.parser import isoparse
from hmd_meta_types import Entity
from hmd_meta_types.entity import ValidationException


class TestNoun:
    def test_namespace_name(self, anoun):
        assert anoun.get_namespace_name() == "name.space.a_noun"

    def test_okay(self, anoun):
        datetime_value = datetime.now().astimezone()
        dict_value = {"one": "two", "three": 4}
        list_value = ["one", 2, 3.0]
        bytes_value = "1234".encode("latin-1")
        noun1 = anoun(
            **{
                "field1": "hello",
                "field2": 5,
                "field3": "b",
                "timestampfield": datetime_value,
                "dictfield": dict_value,
                "listfield": list_value,
                "blobfield": bytes_value,
                "_created": datetime.utcnow(),
                "_updated": datetime.utcnow(),
            }
        )
        assert noun1.field1 == "hello"
        assert noun1.field2 == 5
        assert noun1.field3 == "b"
        assert noun1.timestampfield == datetime_value
        assert noun1.dictfield == dict_value
        assert noun1.listfield == list_value
        assert noun1.blobfield == bytes_value

        assert noun1.serialize() == {
            "field1": "hello",
            "field2": 5,
            "field3": "b",
            "timestampfield": datetime_value.astimezone(timezone.utc).isoformat(),
            "dictfield": b64encode(dumps(dict_value).encode("latin-1")).decode(
                "latin-1"
            ),
            "listfield": b64encode(dumps(list_value).encode("latin-1")).decode(
                "latin-1"
            ),
            "blobfield": b64encode(bytes_value).decode("latin-1"),
            "_created": noun1._created.isoformat(),
            "_updated": noun1._updated.isoformat(),
        }

        new_noun1 = Entity.deserialize(anoun, noun1.serialize())
        assert new_noun1 == noun1

    def test_internal_fields(self, anoun):
        datetime_value = datetime.now().astimezone()
        dict_value = {"one": "two", "three": 4}
        list_value = ["one", 2, 3.0]
        bytes_value = "1234".encode("latin-1")
        updated = datetime.now().astimezone(timezone(timedelta(hours=5)))
        noun1 = anoun(
            **{
                "_updated": updated,
                "_created": updated,
                "field1": "hello",
                "field2": 5,
                "field3": "b",
                "timestampfield": datetime_value,
                "dictfield": dict_value,
                "listfield": list_value,
                "blobfield": bytes_value,
            }
        )
        assert noun1._updated == updated
        assert noun1._created == updated
        assert noun1.field1 == "hello"
        assert noun1.field2 == 5
        assert noun1.field3 == "b"
        assert noun1.timestampfield == datetime_value
        assert noun1.dictfield == dict_value
        assert noun1.listfield == list_value
        assert noun1.blobfield == bytes_value

    def test_instance_type(self, anoun):
        noun1 = anoun(**{"field1": "hello", "field2": 5})

        assert noun1.instance_type == anoun

    def test_bad_type(self, anoun):
        with pytest.raises(
            Exception,
            match='For field, field1, expected a value of one of the types: "str", was "int"',
        ) as exc:
            noun1 = anoun(**{"field1": 5, "field2": 5})

    def test_missing_required_field(self, anoun):
        with pytest.raises(
            Exception, match="Missing required fields: {'field1'}"
        ) as exc:
            noun1 = anoun(**{"field2": 5})

    def test_bad_enum_type(self, anoun):
        with pytest.raises(
            Exception,
            match=re.escape("For field, field3, expected one of ['a', 'b'], was \"c\""),
        ) as exc:
            noun1 = anoun(**{"field1": "hello", "field2": 5, "field3": "c"})

    def test_bad_date_type(self, anoun):
        with pytest.raises(
            Exception,
            match='For field, timestampfield, expected a value of one of the types: "datetime", was "int"',
        ) as exc:
            noun1 = anoun(**{"field1": "hello", "timestampfield": 5})

    def test_timestamp(self, anoun):
        time_string = "1985-12-01T00:00:00Z"
        timestamp = isoparse(time_string)
        noun1 = anoun(**{"field1": "hello", "timestampfield": timestamp})

        assert isinstance(noun1.timestampfield, datetime)
        assert noun1.timestampfield == timestamp

        assert noun1.serialize() == {
            "field1": "hello",
            "timestampfield": timestamp.isoformat(),
        }

        # a datetime in the local timezone
        a_datetime = datetime.now().astimezone(timezone(timedelta(hours=5)))
        noun1.timestampfield = a_datetime

        # confirm the offset from utc is non-zero
        assert a_datetime.tzinfo.utcoffset(noun1.timestampfield).seconds > 0
        # confirm the datetime object in noun1 has a zero offset (because it's in utc)
        assert noun1.timestampfield.tzinfo.utcoffset(noun1.timestampfield) == timedelta(
            0
        )
        # confirm the two dates are equal
        assert a_datetime == noun1.timestampfield

        assert noun1.timestampfield.isoformat() != a_datetime.isoformat()
        assert (
            noun1.timestampfield.isoformat()
            == a_datetime.astimezone(timezone.utc).isoformat()
        )

    def test_set_equals(self, anoun):
        noun1 = anoun(**{"field1": "hello", "field2": 5})
        noun2 = anoun(**{"field1": "hello, world"})

        noun1.set_equals(noun2)
        assert noun1 is not noun2
        assert noun1 == noun2

    def test_deserialize_with_schema_key(self, anoun):
        datetime_value = datetime.now().astimezone()
        dict_value = {"one": "two", "three": 4}
        list_value = ["one", 2, 3.0]
        bytes_value = "1234".encode("latin-1")
        noun1 = anoun(
            **{
                "field1": "hello",
                "field2": 5,
                "field3": "b",
                "timestampfield": datetime_value,
                "dictfield": dict_value,
                "listfield": list_value,
                "blobfield": bytes_value,
                "_created": datetime.utcnow(),
                "_updated": datetime.utcnow(),
            }
        )
        assert noun1.field1 == "hello"
        assert noun1.field2 == 5
        assert noun1.field3 == "b"
        assert noun1.timestampfield == datetime_value
        assert noun1.dictfield == dict_value
        assert noun1.listfield == list_value
        assert noun1.blobfield == bytes_value

        assert noun1.serialize(include_schema=True) == {
            "field1": "hello",
            "field2": 5,
            "field3": "b",
            "timestampfield": datetime_value.astimezone(timezone.utc).isoformat(),
            "dictfield": b64encode(dumps(dict_value).encode("latin-1")).decode(
                "latin-1"
            ),
            "listfield": b64encode(dumps(list_value).encode("latin-1")).decode(
                "latin-1"
            ),
            "blobfield": b64encode(bytes_value).decode("latin-1"),
            "_created": noun1._created.isoformat(),
            "_updated": noun1._updated.isoformat(),
            "__schema": anoun.get_namespace_name(),
        }

        new_noun1 = Entity.deserialize(anoun, noun1.serialize())
        assert new_noun1 == noun1

    def test_attr_validation(self, validation_noun, validation_rel):
        valid_date_str = "2024-02-24"
        valid_time_str = "09:25:03"
        valid_regex_str = "foo-BAR"
        valid_int = 25
        datetime_value = datetime.now().astimezone()
        dict_value = {"one": "two", "three": 4}
        list_value = ["one", 2, 3.0]
        bytes_value = "1234".encode("latin-1")

        valid_noun = validation_noun(
            **{
                "date_str": valid_date_str,
                "time_str": valid_time_str,
                "regex_str": valid_regex_str,
                "field2": valid_int,
                "field3": "b",
                "timestampfield": datetime_value,
                "dictfield": dict_value,
                "listfield": list_value,
                "blobfield": bytes_value,
                "_created": datetime.utcnow(),
                "_updated": datetime.utcnow(),
            }
        )

        assert valid_noun.date_str == valid_date_str
        assert valid_noun.time_str == valid_time_str
        assert valid_noun.regex_str == valid_regex_str
        assert valid_noun.field2 == valid_int

        invalid_date_str = "20240224"
        invalid_time_str = "09-25:03.333"
        invalid_regex_str = "Foo-BAR"
        invalid_int = 5
        datetime_value = datetime.now().astimezone()
        dict_value = {"one": "two", "three": 4}
        list_value = ["one", 2, 3.0]
        bytes_value = "1234".encode("latin-1")

        with pytest.raises(ValidationException):
            valid_noun = validation_noun(
                **{
                    "date_str": invalid_date_str,
                    "time_str": invalid_time_str,
                    "regex_str": invalid_regex_str,
                    "field2": invalid_int,
                    "field3": "b",
                    "timestampfield": datetime_value,
                    "dictfield": dict_value,
                    "listfield": list_value,
                    "blobfield": bytes_value,
                    "_created": datetime.utcnow(),
                    "_updated": datetime.utcnow(),
                }
            )
