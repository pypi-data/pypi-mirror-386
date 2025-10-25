# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""API types"""

from dataclasses import dataclass
from typing import Any, Literal

from cascade.low.core import JobInstance
from forecastbox.products.product import USER_DEFINED
from pydantic import BaseModel, Field, PositiveInt, field_validator, model_validator

CONFIG_ORDER = ["param", "levtype", "levelist"]

ModelName = str


class FIABBaseModel(BaseModel):
    pass


class ModelSpecification(FIABBaseModel):
    model: ModelName
    date: str
    lead_time: int
    ensemble_members: int
    # entries: dict[str, str] = Field(default_factory=dict)

    @field_validator("model")
    def model_cleanup(cls, m):
        return m.lower().replace("_", "/")


class ConfigEntry(FIABBaseModel):
    label: str
    """Label of the configuration entry"""
    description: str | None
    """Description of the configuration entry"""
    values: list[Any] | None = None
    """Available values for the configuration entry"""
    example: str | None = None
    """Example value for the configuration entry"""
    multiple: bool = False
    """Whether the configuration entry is a multiple select"""
    constrained_by: list[str] = Field(default_factory=list)
    """List of configuration entries that this entry is constrained by"""
    default: str | None = None

    @model_validator(mode="after")
    def __post_init__(self):
        if self.values and USER_DEFINED in self.values:
            self.values = None

        if self.values is None:
            self.multiple = False
        else:
            self._sort_values()
        return self

    def _sort_values(self):
        if all(str(x).isdigit() for x in self.values):
            self.values = list(map(str, sorted(self.values, key=float)))
            return
        self.values = list(map(str, sorted(self.values, key=lambda x: str(x).lower())))


class ProductConfiguration(FIABBaseModel):
    """Product Configuration

    Provides the available configuration entries for a product.
    """

    product: str
    options: dict[str, ConfigEntry]

    @model_validator(mode="after")
    def sort_values(self):
        new_options = {}
        for key in CONFIG_ORDER:
            if key in self.options:
                new_options[key] = self.options[key]

        for key in self.options:
            if key not in new_options:
                new_options[key] = self.options[key]

        self.options = new_options
        return self


@dataclass
class ProductSpecification:
    product: str
    specification: dict[str, Any]


class EnvironmentSpecification(FIABBaseModel):
    hosts: PositiveInt | None = Field(default=None)
    workers_per_host: PositiveInt | None = Field(default=None)
    environment_variables: dict[str, str] = Field(default_factory=dict)


class ForecastProducts(FIABBaseModel):
    job_type: Literal["forecast_products"]
    model: ModelSpecification
    products: list[ProductSpecification]


class RawCascadeJob(FIABBaseModel):
    job_type: Literal["raw_cascade_job"]
    job_instance: JobInstance


class ExecutionSpecification(FIABBaseModel):
    job: ForecastProducts | RawCascadeJob = Field(discriminator="job_type")
    environment: EnvironmentSpecification
    shared: bool = Field(default=False)


class VisualisationOptions(FIABBaseModel):
    preset: str = "blob"
    # width: str | int = '100%'
    # height: str | int = 600
