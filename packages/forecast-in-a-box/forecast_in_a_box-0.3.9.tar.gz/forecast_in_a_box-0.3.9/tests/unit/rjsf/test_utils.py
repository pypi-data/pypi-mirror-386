from forecastbox.rjsf import utils
from forecastbox.rjsf.forms import FieldWithUI
from forecastbox.rjsf.jsonSchema import ArraySchema, EnumMixin, StringSchema
from forecastbox.rjsf.uiSchema import UIField, UIObjectField


def test_update_enum_within_field_string():
    field = FieldWithUI(jsonschema=StringSchema(type="string", title="Color"), uischema=None)
    updated = utils.update_enum_within_field(field, ["red", "green"])
    assert isinstance(updated.jsonschema, EnumMixin)
    assert updated.jsonschema.enum == ["red", "green"]


def test_update_enum_within_field_array():
    arr = ArraySchema(type="array", title="Arr", items=StringSchema(type="string", title="Item"))
    field = FieldWithUI(jsonschema=arr, uischema=None)
    updated = utils.update_enum_within_field(field, ["a", "b"])
    assert isinstance(updated.jsonschema, ArraySchema)
    assert isinstance(updated.jsonschema.items, EnumMixin)
    assert updated.jsonschema.items.enum == ["a", "b"]


def test_collapse_enums_if_possible_string():
    field = FieldWithUI(jsonschema=StringSchema(type="string", title="X", enum=["only"]), uischema=None)  # type: ignore
    collapsed = utils.collapse_enums_if_possible(field)
    assert collapsed.jsonschema.default == "only"
    assert isinstance(collapsed.uischema, UIField)
    assert collapsed.uischema.disabled is True


def test_collapse_enums_if_possible_array():
    arr = ArraySchema(type="array", title="Arr", items=StringSchema(type="string", title="Item", enum=["one"]))  # type: ignore
    field = FieldWithUI(jsonschema=arr, uischema=None)
    collapsed = utils.collapse_enums_if_possible(field)
    assert isinstance(collapsed.jsonschema, ArraySchema)
    assert collapsed.jsonschema.items.default == "one"
    assert isinstance(collapsed.uischema, UIObjectField)
    assert hasattr(collapsed.uischema, "anyOf")


def test_collapse_enums_if_possible_noop():
    # Should not collapse if more than one enum value
    field = FieldWithUI(jsonschema=StringSchema(type="string", title="X", enum=["a", "b"]), uischema=None)  # type: ignore
    result = utils.collapse_enums_if_possible(field)
    assert result is field
    # Should not collapse if no enum
    field2 = FieldWithUI(jsonschema=StringSchema(type="string", title="X"), uischema=None)
    result2 = utils.collapse_enums_if_possible(field2)
    assert result2 is field2
