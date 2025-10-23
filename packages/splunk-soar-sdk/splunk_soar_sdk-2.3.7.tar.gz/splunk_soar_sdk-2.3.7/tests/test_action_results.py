from typing import Optional, Union
import pytest
from soar_sdk.action_results import ActionOutput, OutputField


class ExampleInnerData(ActionOutput):
    inner_string: str = OutputField(
        example_values=["example_value_1", "example_value_2"]
    )


class ExampleActionOutput(ActionOutput):
    under_field: str = OutputField(alias="_under_field")
    stringy_field: str
    list_of_strings: list[str]
    nested_lists: list[list[int]]
    cef_data: str = OutputField(
        cef_types=["ip"], example_values=["192.168.0.1", "1.1.1.1"]
    )
    nested_type: ExampleInnerData
    list_of_types: list[ExampleInnerData]
    optional_field: Optional[str]
    optional_inner_field: Optional[ExampleInnerData]
    optional_list_of_types: Optional[list[ExampleInnerData]]


def test_action_output_to_json_schema():
    expected_schema = [
        {"data_path": "action_result.data.*._under_field", "data_type": "string"},
        {"data_path": "action_result.data.*.stringy_field", "data_type": "string"},
        {"data_path": "action_result.data.*.list_of_strings.*", "data_type": "string"},
        {"data_path": "action_result.data.*.nested_lists.*.*", "data_type": "numeric"},
        {
            "data_path": "action_result.data.*.cef_data",
            "data_type": "string",
            "contains": ["ip"],
            "example_values": ["192.168.0.1", "1.1.1.1"],
        },
        {
            "data_path": "action_result.data.*.nested_type.inner_string",
            "data_type": "string",
            "example_values": ["example_value_1", "example_value_2"],
        },
        {
            "data_path": "action_result.data.*.list_of_types.*.inner_string",
            "data_type": "string",
            "example_values": ["example_value_1", "example_value_2"],
        },
        {"data_path": "action_result.data.*.optional_field", "data_type": "string"},
        {
            "data_path": "action_result.data.*.optional_inner_field.inner_string",
            "data_type": "string",
            "example_values": ["example_value_1", "example_value_2"],
        },
        {
            "data_path": "action_result.data.*.optional_list_of_types.*.inner_string",
            "data_type": "string",
            "example_values": ["example_value_1", "example_value_2"],
        },
    ]

    schema = list(ExampleActionOutput._to_json_schema())
    assert schema == expected_schema


class BadActionOutput(ActionOutput):
    byte_field: bytes


class BadUnionActionOutput(ActionOutput):
    union_field: Union[str, int]


class BadOptionalUnionActionOutput(ActionOutput):
    evil_field: Optional[Union[str, int]]


class BadListOfNonesActionOutput(ActionOutput):
    list_of_nones: list[None]


class BadWeirdListActionOutput(ActionOutput):
    list_of_wat: list[str, int, float, None]


@pytest.mark.parametrize(
    "action_output_class, expected_message",
    [
        (BadActionOutput, "Unsupported field type"),
        (BadUnionActionOutput, "only valid Union type"),
        (BadOptionalUnionActionOutput, "only valid Union type"),
        (BadListOfNonesActionOutput, "must have exactly one"),
        (BadWeirdListActionOutput, "must have exactly one"),
    ],
)
def test_action_output_to_json_schema_bad_type(
    action_output_class: type[ActionOutput], expected_message: str
):
    with pytest.raises(TypeError, match=expected_message):
        next(action_output_class._to_json_schema())


def test_parse_action_output():
    raw_data = {
        "_under_field": "example_value",
        "stringy_field": "example_string",
        "list_of_strings": ["string1", "string2"],
        "nested_lists": [[1, 2], [3, 4]],
        "cef_data": "42.42.42.42",
        "nested_type": {"inner_string": "inner_value"},
        "list_of_types": [
            {"inner_string": "inner_value_1"},
            {"inner_string": "inner_value_2"},
        ],
    }
    parsed_data = ExampleActionOutput.parse_obj(raw_data)
    assert parsed_data.stringy_field == "example_string"
    assert parsed_data.list_of_strings == ["string1", "string2"]
    assert parsed_data.nested_lists == [[1, 2], [3, 4]]
    assert parsed_data.cef_data == "42.42.42.42"
    assert parsed_data.nested_type.inner_string == "inner_value"
    assert len(parsed_data.list_of_types) == 2
    assert parsed_data.list_of_types[0].inner_string == "inner_value_1"
    assert parsed_data.list_of_types[1].inner_string == "inner_value_2"


def test_action_output_to_dict():
    action_output = ExampleActionOutput(
        _under_field="example_value",
        stringy_field="example_string",
        list_of_strings=["string1", "string2"],
        nested_lists=[[1, 2], [3, 4]],
        cef_data="42.42.42.42",
        nested_type=ExampleInnerData(inner_string="inner_value"),
        list_of_types=[
            ExampleInnerData(inner_string="inner_value_1"),
            ExampleInnerData(inner_string="inner_value_2"),
        ],
    )
    expected_dict = {
        "_under_field": "example_value",
        "stringy_field": "example_string",
        "list_of_strings": ["string1", "string2"],
        "nested_lists": [[1, 2], [3, 4]],
        "cef_data": "42.42.42.42",
        "nested_type": {"inner_string": "inner_value"},
        "list_of_types": [
            {"inner_string": "inner_value_1"},
            {"inner_string": "inner_value_2"},
        ],
        "optional_field": None,
        "optional_inner_field": None,
        "optional_list_of_types": None,
    }
    assert action_output.dict(by_alias=True) == expected_dict


def test_action_output_to_json_schema_with_column_name_and_column_order():
    class ExampleActionOutputWithColumnNames(ActionOutput):
        stringy_field: str = OutputField(column_name="Stringy Field")

    schema = list(ExampleActionOutputWithColumnNames._to_json_schema())
    assert schema == [
        {
            "data_path": "action_result.data.*.stringy_field",
            "data_type": "string",
            "column_name": "Stringy Field",
            "column_order": 0,
        }
    ]
