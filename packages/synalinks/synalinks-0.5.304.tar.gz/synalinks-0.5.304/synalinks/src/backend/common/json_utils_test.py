# License Apache 2.0: (c) 2025 Yoan Sallami (Synalinks Team)

from typing import List
from typing import Literal
from typing import Union

from synalinks.src import testing
from synalinks.src.backend import DataModel
from synalinks.src.backend import concatenate_json
from synalinks.src.backend import factorize_json
from synalinks.src.backend import in_mask_json
from synalinks.src.backend import out_mask_json


class JsonConcatenateTest(testing.TestCase):
    def test_concatenate_identical_jsons(self):
        class Input(DataModel):
            foo: str

        class Result(DataModel):
            foo: str
            foo_1: str

        json = Input(foo="test").get_json()
        expected = Result(foo="test", foo_1="test").get_json()

        result = concatenate_json(json, json)
        self.assertEqual(result, expected)

    def test_concatenate_jsons_with_different_properties(self):
        class Input1(DataModel):
            foo: str

        class Input2(DataModel):
            bar: str

        class Result(DataModel):
            foo: str
            bar: str

        json1 = Input1(foo="test").get_json()

        json2 = Input2(bar="test").get_json()

        expected = Result(foo="test", bar="test").get_json()

        result = concatenate_json(json1, json2)
        self.assertEqual(result, expected)

    def test_concatenate_json_multiple_times(self):
        class Input(DataModel):
            foo: str

        class Result(DataModel):
            foo: str
            foo_1: str
            foo_2: str

        json = Input(foo="test").get_json()
        expected = Result(foo="test", foo_1="test", foo_2="test").get_json()

        result = concatenate_json(json, json)
        result = concatenate_json(result, json)
        self.assertEqual(result, expected)

    def test_concatenate_nested(self):
        class BarObject(DataModel):
            foo: str
            bar: str

        class Input(DataModel):
            bar: BarObject

        class Result(DataModel):
            bar: BarObject
            bar_1: BarObject

        json = Input(bar=BarObject(foo="test", bar="test")).get_json()
        expected = Result(
            bar=BarObject(foo="test", bar="test"),
            bar_1=BarObject(foo="test", bar="test"),
        ).get_json()

        result = concatenate_json(json, json)
        self.assertEqual(result, expected)

    def test_concatenate_similar_entities(self):
        class City(DataModel):
            label: Literal["City"]
            name: str

        class Cities(DataModel):
            entities: List[City]

        class Result(DataModel):
            entities: List[City]
            entities_1: List[City]

        paris = City(label="City", name="Paris")
        toulouse = City(label="City", name="Toulouse")

        json = Cities(entities=[paris, toulouse]).get_json()
        expected = Result(
            entities=[paris, toulouse],
            entities_1=[paris, toulouse],
        ).get_json()

        result = concatenate_json(json, json)
        self.assertEqual(result, expected)

    def test_concatenate_different_entities(self):
        class City(DataModel):
            label: Literal["City"]
            name: str

        class Event(DataModel):
            label: Literal["Event"]
            name: str

        class Cities(DataModel):
            entities: List[City]

        class Events(DataModel):
            entities: List[Event]

        class Result(DataModel):
            entities: List[City]
            entities_1: List[Event]

        paris = City(label="City", name="Paris")
        toulouse = City(label="City", name="Toulouse")

        event1 = Event(label="Event", name="A test event")
        event2 = Event(label="Event", name="Another test event")

        json1 = Cities(entities=[paris, toulouse]).get_json()
        json2 = Events(entities=[event1, event2]).get_json()

        expected = Result(
            entities=[paris, toulouse],
            entities_1=[event1, event2],
        ).get_json()

        result = concatenate_json(json1, json2)
        self.assertEqual(result, expected)


class JsonFactorizeTest(testing.TestCase):
    def test_factorize_json_with_identical_properties(self):
        class Input(DataModel):
            foo: str
            foo_1: str

        class Result(DataModel):
            foos: List[str]

        json = Input(foo="test", foo_1="test").get_json()
        expected = Result(foos=["test", "test"]).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_json_with_multiple_identical_properties(self):
        class Input(DataModel):
            foo: str
            foo_1: str
            foo_2: str

        class Result(DataModel):
            foos: List[str]

        json = Input(foo="test", foo_1="test", foo_2="test").get_json()
        expected = Result(foos=["test", "test", "test"]).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_json_with_different_properties(self):
        class Input(DataModel):
            foo: str
            bar: str

        class Result(DataModel):
            foo: str
            bar: str

        json = Input(foo="test", bar="test").get_json()
        expected = Result(foo="test", bar="test").get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_json_with_mixed_properties(self):
        class Input(DataModel):
            foo: str
            foo_1: str
            bar: str
            boo: str

        class Result(DataModel):
            foos: List[str]
            bar: str
            boo: str

        json = Input(
            foo="test",
            foo_1="test",
            bar="test",
            boo="test",
        ).get_json()

        expected = Result(
            foos=["test", "test"],
            bar="test",
            boo="test",
        ).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_json_with_existing_array_property(self):
        class Input(DataModel):
            foos: List[str]
            foo: str

        class Result(DataModel):
            foos: List[str]

        json = Input(foos=["test"], foo="test").get_json()
        expected = Result(foos=["test", "test"]).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_json_with_existing_array_property_and_additional_properties(
        self,
    ):
        class Input(DataModel):
            foos: List[str]
            foo: str
            foo_1: str

        class Result(DataModel):
            foos: List[str]

        json = Input(
            foos=["test", "test"],
            foo="test",
            foo_1="test",
        ).get_json()

        expected = Result(foos=["test", "test", "test", "test"]).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_json_with_multiple_groups_of_properties(self):
        class Input(DataModel):
            foo: str
            foo_1: str
            bar: str
            bar_1: str

        class Result(DataModel):
            foos: List[str]
            bars: List[str]

        json = Input(
            foo="test",
            foo_1="test",
            bar="test",
            bar_1="test",
        ).get_json()

        expected = Result(
            foos=["test", "test"],
            bars=["test", "test"],
        ).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_nested(self):
        class BarObject(DataModel):
            foo: str
            bar: str

        class Input(DataModel):
            bar: BarObject
            bar_1: BarObject

        class Result(DataModel):
            bars: List[BarObject]

        json = Input(
            bar=BarObject(
                foo="test",
                bar="test",
            ),
            bar_1=BarObject(
                foo="test",
                bar="test",
            ),
        ).get_json()

        expected = Result(
            bars=[
                BarObject(
                    foo="test",
                    bar="test",
                ),
                BarObject(
                    foo="test",
                    bar="test",
                ),
            ]
        ).get_json()

        result = factorize_json(json)
        self.assertEqual(result, expected)

    def test_factorize_similar_entities(self):
        class City(DataModel):
            label: Literal["City"]
            name: str

        class Cities(DataModel):
            entities: List[City]

        class Input(DataModel):
            entities: List[City]
            entities_1: List[City]

        class Result(DataModel):
            entities: List[City]

        paris = City(label="City", name="Paris")
        toulouse = City(label="City", name="Toulouse")

        inputs = Input(
            entities=[paris, toulouse],
            entities_1=[paris, toulouse],
        ).get_json()
        expected = Result(
            entities=[paris, toulouse, paris, toulouse],
        ).get_json()

        result = factorize_json(inputs)
        self.assertEqual(result, expected)

    def test_factorize_different_entities(self):
        class City(DataModel):
            label: Literal["City"]
            name: str

        class Event(DataModel):
            label: Literal["Event"]
            name: str

        class Input(DataModel):
            entities: List[City]
            entities_1: List[Event]

        class Result(DataModel):
            entities: List[Union[City, Event]]

        paris = City(label="City", name="Paris")
        toulouse = City(label="City", name="Toulouse")

        event1 = Event(label="Event", name="A test event")
        event2 = Event(label="Event", name="Another test event")

        inputs = Input(
            entities=[paris, toulouse],
            entities_1=[event1, event2],
        ).get_json()
        expected = Result(
            entities=[paris, toulouse, event1, event2],
        ).get_json()

        result = factorize_json(inputs)
        self.assertEqual(result, expected)


class JsonOutMaskTest(testing.TestCase):
    def test_mask_basic(self):
        class Input(DataModel):
            foo: str
            bar: str

        class Result(DataModel):
            bar: str

        json = Input(foo="test", bar="test").get_json()
        expected = Result(bar="test").get_json()

        result = out_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_multiple_fields_with_same_base_name(self):
        class Input(DataModel):
            foo: str
            foo_1: str
            bar: str
            bar_1: str

        class Result(DataModel):
            bar: str
            bar_1: str

        json = Input(
            foo="test",
            foo_1="str",
            bar="test",
            bar_1="test",
        ).get_json()

        expected = Result(
            bar="test",
            bar_1="test",
        ).get_json()

        result = out_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_nested(self):
        class BarObject(DataModel):
            foo: str
            bar: str

        class Input(DataModel):
            bar: BarObject
            bar_1: BarObject

        json = Input(
            bar=BarObject(
                foo="test",
                bar="test",
            ),
            bar_1=BarObject(
                foo="test",
                bar="test",
            ),
        ).get_json()

        class BarObject(DataModel):
            bar: str

        class Result(DataModel):
            bar: BarObject
            bar_1: BarObject

        expected = Result(
            bar=BarObject(
                bar="test",
            ),
            bar_1=BarObject(
                bar="test",
            ),
        ).get_json()

        result = out_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_deeply_nested(self):
        class BooObject(DataModel):
            foo: str
            boo: str

        class BarObject(DataModel):
            boo: BooObject

        class Input(DataModel):
            foo: str
            bar: BarObject

        json = Input(
            foo="test",
            bar=BarObject(
                boo=BooObject(
                    foo="test",
                    boo="test",
                )
            ),
        ).get_json()

        class BooObject(DataModel):
            boo: str

        class BarObject(DataModel):
            boo: BooObject

        class Result(DataModel):
            bar: BarObject

        expected = Result(
            bar=BarObject(
                boo=BooObject(
                    boo="test",
                )
            )
        ).get_json()

        result = out_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_in_array(self):
        class BooObject(DataModel):
            foo: str
            boo: str

        class Input(DataModel):
            boos: List[BooObject]

        json = Input(
            boos=[
                BooObject(
                    foo="test",
                    boo="test",
                ),
                BooObject(
                    foo="test",
                    boo="test",
                ),
            ]
        ).get_json()

        class BooObject(DataModel):
            boo: str

        class Result(DataModel):
            boos: List[BooObject]

        expected = Result(
            boos=[
                BooObject(
                    boo="test",
                ),
                BooObject(
                    boo="test",
                ),
            ]
        ).get_json()

        result = out_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_empty_json(self):
        class Input(DataModel):
            pass

        class Result(DataModel):
            pass

        json = Input().get_json()
        expected = Result().get_json()

        result = out_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_empty_mask_list(self):
        class Input(DataModel):
            foo: str
            bar: str

        class Result(DataModel):
            foo: str
            bar: str

        json = Input(foo="test", bar="test").get_json()
        expected = Result(foo="test", bar="test").get_json()

        result = out_mask_json(json, mask=[])
        self.assertEqual(result, expected)

    def test_mask_non_recursive(self):
        class BooObject(DataModel):
            foo: str
            boo: str

        class Input(DataModel):
            foo: str
            boo: BooObject

        json = Input(
            foo="test",
            boo=BooObject(foo="test", boo="test"),
        ).get_json()

        class Result(DataModel):
            boo: BooObject

        expected = Result(
            boo=BooObject(
                foo="test",
                boo="test",
            )
        ).get_json()

        result = out_mask_json(json, mask=["foo"], recursive=False)
        self.assertEqual(result, expected)


class JsonInMaskTest(testing.TestCase):
    def test_mask_basic(self):
        json = {
            "foo": "test",
            "bar": "test",
        }

        expected = {
            "foo": "test",
        }

        result = in_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_keep_all(self):
        json = {
            "foo": "test",
            "foos": "test",
            "bar": "test",
        }

        expected = {
            "foo": "test",
            "foos": "test",
            "bar": "test",
        }

        result = in_mask_json(json, mask=["foos", "bar"])
        self.assertEqual(result, expected)

    def test_mask_multiple_fields_with_same_base_name(self):
        json = {"foo": "test", "foo_1": "test", "bar": "test", "bar_1": "test"}

        expected = {"foo": "test", "foo_1": "test"}

        result = in_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_nested(self):
        json = {
            "foo": "test",
            "foo_1": "test",
            "bar": {"foo": "test", "bar": "test"},
            "bar_1": "test",
        }

        expected = {"foo": "test", "foo_1": "test"}

        result = in_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_deeply_nested(self):
        json = {"foo": "test", "bar": {"bar": {"foo": "test", "qux": "test"}}}

        expected = {"foo": "test", "bar": {"bar": {"foo": "test"}}}

        result = in_mask_json(json, mask=["foo", "bar"])
        self.assertEqual(result, expected)

    def test_mask_in_array(self):
        json = {
            "items": [
                {"foo": "test", "bar": "test"},
                {"foo_1": "test", "bar_1": "test"},
            ]
        }

        expected = {"items": [{"foo": "test"}, {"foo_1": "test"}]}

        result = in_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_empty_json(self):
        json = {}
        expected = {}

        result = in_mask_json(json, mask=["foo"])
        self.assertEqual(result, expected)

    def test_mask_empty_mask_list(self):
        json = {"foo": "test", "bar": "test"}

        expected = {}

        result = in_mask_json(json, mask=[])
        self.assertEqual(result, expected)

    def test_mask_non_recursive(self):
        json = {"foo": "test", "bar": {"foo": "test", "bar": "test"}}

        expected = {"foo": "test"}

        result = in_mask_json(json, mask=["foo"], recursive=False)
        self.assertEqual(result, expected)
