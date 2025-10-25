# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

# A pydantic implementation of JSON Schema for React JSON Schema Form (RJSF).
# This schema defines the structure of data as expected by RJSF based on the JSON Schema specification.
# https://rjsf-team.github.io/react-jsonschema-form/docs/

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


# Base Schema with discriminator
class BaseSchema(BaseModel):
    """Base class for all JSON Schema types.

    Examples
    --------
    >>> BaseSchema(title="Example", description="A base schema", default=None)
    """

    type: str | list[str]
    """Type of the schema (e.g., 'string', 'object', etc.)."""
    title: str | None = None
    """Title of the schema."""
    description: str | None = None
    """Description of the schema."""
    default: Any | None = None
    """Default value for the schema."""
    additionalProperties: "FieldSchema | None" = None
    """Additional properties allowed in the schema."""

    model_config = ConfigDict(extra="allow", use_enum_values=True, json_schema_extra={"discriminator": "type"})

    def update(self, *a, **k):
        pass


class EnumMixin:
    """Mixin for schemas that can have an enum.

    Examples
    --------
    >>> class MyEnumSchema(EnumMixin):
    ...     enum = ["a", "b", "c"]
    ...
    >>> s = MyEnumSchema()
    >>> s.update_enum(["x", "y"])
    """

    enum: list[Any] | None = None
    """list of allowed values for the schema."""

    def update_enum(self, new_enum: list[Any]):
        if not isinstance(new_enum, list):
            raise TypeError("Enum must be a list")
        self.enum = new_enum


class StringSchema(BaseSchema, EnumMixin):
    """JSON Schema for string type.

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/string.html

    Examples
    --------
    >>> StringSchema(type="string", title="Name", minLength=1, maxLength=10)
    >>> StringSchema(type="string", enum=["a", "b"])
    """

    type: str | list[str] | Literal["string"] = Field(default="string")
    format: str | None = None
    """String format (e.g., 'date', 'email')."""
    minLength: int | None = None
    """Minimum length."""
    maxLength: int | None = None
    """Maximum length."""


class IntegerSchema(BaseSchema, EnumMixin):
    """JSON Schema for integer type.

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/numeric.html

    Examples
    --------
    >>> IntegerSchema(type="integer", minimum=0, maximum=100)
    >>> IntegerSchema(type="integer", enum=[1, 2, 3])
    """

    type: str | list[str] | Literal["integer"] = Field(default="integer")
    minimum: int | None = None
    """Minimum value."""
    maximum: int | None = None
    """Maximum value."""
    multipleOf: int | None = None
    """Value must be a multiple of this number."""


class NumberSchema(BaseSchema, EnumMixin):
    """JSON Schema for number type (float or int).

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/numeric.html

    Examples
    --------
    >>> NumberSchema(type="number", minimum=0.0, maximum=10.0)
    >>> NumberSchema(type="number", enum=[1.1, 2.2])
    """

    type: str | list[str] | Literal["number"] = Field(default="number")
    """Must be 'number'."""
    minimum: float | None = None
    """Minimum value."""
    maximum: float | None = None
    """Maximum value."""


class BooleanSchema(BaseSchema):
    """JSON Schema for boolean type.

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/boolean.html

    Examples
    --------
    >>> BooleanSchema(type="boolean")
    """

    type: str | list[str] | Literal["boolean"] = Field(default="boolean")


class NullSchema(BaseSchema):
    """JSON Schema for null type.

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/null.html

    Examples
    --------
    >>> NullSchema(type="null")
    """

    type: str | list[str] | Literal['null'] = Field(default="null")


class ObjectSchema(BaseSchema):
    """JSON Schema for object type.

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/object.html

    Examples
    --------
    >>> ObjectSchema(type="object", properties={"name": StringSchema(type="string")}, required=["name"])
    """

    type: str | list[str] | Literal["object"] = Field(default="object")
    properties: dict[str, "FieldSchema"] = Field(default_factory=dict)
    """Underlying fields of the object."""
    required: list[str] | None = None
    """list of required property names."""

    anyOf: list["FieldSchema"] | None = None
    oneOf: list["FieldSchema"] | None = None
    allOf: list["FieldSchema"] | None = None


class ArraySchema(BaseSchema):
    """JSON Schema for array type.

    See Also
    --------
    https://json-schema.org/understanding-json-schema/reference/array.html

    Examples
    --------
    >>> ArraySchema(type="array", items=StringSchema(type="string", enum=["test", "wow"]), minItems=1)
    """

    type: str | list[str] | Literal["array"] = Field(default="array")
    items: "FieldSchema"
    """Schema for array items."""
    minItems: int | None = None
    """Minimum number of items."""
    maxItems: int | None = None
    """Maximum number of items."""
    uniqueItems: bool | None = None
    """Whether all items must be unique."""


FieldSchema = Union[
    StringSchema,
    IntegerSchema,
    BooleanSchema,
    NumberSchema,
    NullSchema,
    ObjectSchema,
    ArraySchema,
]
"""Union type for all JSON Schema field types."""

BaseSchema.model_rebuild()
ObjectSchema.model_rebuild()
ArraySchema.model_rebuild()


__all__ = [
    "StringSchema",
    "IntegerSchema",
    "BooleanSchema",
    "ObjectSchema",
    "FieldSchema",
    "ArraySchema",
    "NumberSchema",
    "NullSchema",
]
