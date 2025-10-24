from __future__ import annotations

import datetime as dt
import json
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Any, Dict, List, Literal, Optional, Self, Sequence, Union

import httpx
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, model_validator

from fbnconfig.property import PropertyKey

from .resource_abc import CamelAlias, Ref, Resource, register_resource


class MetricValue(CamelAlias, BaseModel):
    value: float
    unit: Optional[str] = None


def des_isodate(value: str | dt.datetime) -> dt.datetime:
    """Deserialize ISO 8601 date string to datetime object."""
    if isinstance(value, dt.datetime):
        return value.astimezone(tz=dt.timezone.utc)
    return dt.datetime.fromisoformat(value)


def ser_isodate(value: dt.datetime) -> str:
    """Serialize datetime object to ISO 8601 string."""
    return value.isoformat()


IsoDateTime = Annotated[
    dt.datetime | dt.date,
    BeforeValidator(des_isodate), PlainSerializer(ser_isodate)
]


class PropertyValue(CamelAlias, BaseModel):
    property_key: PropertyKey = Field(serialization_alias="propertyKey")
    label_value: Optional[str] = Field(default=None, serialization_alias="labelValue")
    metric_value: Optional[MetricValue] = Field(default=None, serialization_alias="metricValue")
    label_set_value: Optional[List[str]] = Field(default=None, serialization_alias="labelSetValue")
    effective_from: IsoDateTime | None = None
    effective_until: IsoDateTime | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info):
        if not isinstance(data, dict):
            return data
        style = info.context.get("style", "api") if info.context else "api"
        if style == "api" and data.get("value", None):
            return data | data["value"]
        return data

    @model_validator(mode="after")
    def validate_one_value_exists(self) -> Self:
        fields = ["label_value", "metric_value", "label_set_value"]
        s = [field for field in fields if getattr(self, field) is not None]
        if len(s) > 1:
            raise KeyError(f"Cannot set {' and '.join(s)}, only one of {' or '.join(fields)} can be set")

        return self


def serialize_properties_as_dict(values: List[PropertyValue], info):
    style = info.context.get("style", "api") if info.context else "api"
    if style == "dump":
        return values
    property_dict = {}
    for prop in values:
        value = {}
        if prop.label_value:
            value["labelValue"] = prop.label_value
        elif prop.metric_value:
            value["metricValue"] = prop.metric_value
        elif prop.label_set_value:
            value["labelSetValue"] = prop.label_set_value
        key = f"{prop.property_key.domain.value}/{prop.property_key.scope}/{prop.property_key.code}"
        property_dict[key] = {"key": key, "value": value}

        if prop.effective_from is not None:
            property_dict[key]["effectiveFrom"] = prop.effective_from

        if prop.effective_until is not None:
            property_dict[key]["effectiveUntil"] = prop.effective_until

    return property_dict


def des_properties_dict(data, info) -> Sequence[PropertyValue] | Dict | None:
    if not isinstance(data, dict) or data is None:
        return data
    style = info.context.get("style", "api") if info.context else "api"
    if style == "api" and isinstance(data, dict):
        data = [value | {"propertyKey": value["key"]} for value in data.values()]
    return data


PropertyValueDict = Annotated[
    Sequence[PropertyValue],
    BeforeValidator(des_properties_dict), PlainSerializer(serialize_properties_as_dict)
]


@register_resource()
class ChartOfAccountsRef(BaseModel, Ref):
    """Reference an chart of account

    Example
    -------
    >>> from fbnconfig.fund_accounting import ChartOfAccountsRef
    >>> chart_of_account = ChartOfAccountsRef(
    >>> id="chart_example",
    >>> code="code_example",
    >>> scope="scope_example")
    """

    id: str = Field(exclude=True, init=True)
    code: str
    scope: str

    def attach(self, client):
        try:
            client.request("get", f"/api/api/chartofaccounts/{self.scope}/{self.code}")
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Chart of Accounts {self.scope}/{self.code} not found")
            else:
                raise ex


@register_resource()
class ChartOfAccountsResource(CamelAlias, BaseModel, Resource):
    """Define a Chart of Account in LUSID"""

    id: str = Field(exclude=True)
    scope: str
    code: str
    display_name: str | None = None
    description: str | None = None
    properties: PropertyValueDict | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # promote scope and code to top for api style
        if "id" in data and isinstance(data["id"], dict):
            data = data | data["id"]
            data.pop("id", None)
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}

        return data

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> None | Dict[str, Any]:
        # Get the property keys to get all properties existing in the chart of accounts
        scope = old_state.scope
        code = old_state.code
        properties = client.get(f"/api/api/chartofaccounts/{scope}/{code}/properties").json()

        params = []
        if "properties" in properties:
            property_keys_list = []
            for key in properties["properties"]:
                property_keys_list.append(key)

            params = [("propertyKeys", prop_key) for prop_key in property_keys_list]

        response = client.get(f"/api/api/chartofaccounts/{scope}/{code}", params=params).json()

        # Remove unnecessary fields
        response.pop("href", None)
        response.pop("links", None)
        return response

    def create(self, client: httpx.Client) -> Optional[Dict[str, Any]]:
        desired = self.model_dump(mode="json", exclude_none=True, by_alias=True, exclude={"scope"})
        response = client.post(f"/api/api/chartofaccounts/{self.scope}", json=desired).json()
        remote_version = response["version"]["asAtVersionNumber"]

        # Remove unnecessary fields
        response.pop("href", None)
        response.pop("links", None)

        return {
            "scope": self.scope,
            "code": self.code,
            "source_version": self.__get_content_hash__(),
            "remote_version": remote_version,
        }

    def update(self, client: httpx.Client, old_state) -> Union[None, Dict[str, Any]]:
        if (self.scope, self.code) != (old_state.scope, old_state.code):
            self.delete(client, old_state)
            return self.create(client)

        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)

        remote_hash = None
        if remote is not None:
            remote_hash = remote["version"]["asAtVersionNumber"]

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        self.delete(client, old_state)
        return self.create(client)

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:
        client.delete(f"/api/api/chartofaccounts/{old_state.scope}/{old_state.code}")

    def deps(self):
        deps = []
        if self.properties is None:
            return deps

        for perp_prop in self.properties:
            deps.append(perp_prop.property_key)

        return deps


def ser_chart_of_account_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return {"scope": value.scope, "code": value.code}


def des_chart_of_account_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


ChartOfAccountsKey = Annotated[
    ChartOfAccountsRef | ChartOfAccountsResource,
    BeforeValidator(des_chart_of_account_key), PlainSerializer(ser_chart_of_account_key)
]


class AccountStatus(StrEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"


class AccountType(StrEnum):
    ASSET = "Asset"
    LIABILITIES = "Liabilities"
    INCOME = "Income"
    EXPENSE = "Expense"
    CAPITAL = "Capital"
    REVENUE = "Revenue"


@register_resource()
class AccountRef(CamelAlias, BaseModel, Ref):
    """Reference an account

    Example
    -------
    >>> from fbnconfig.fund_accounting import ChartOfAccountsRef, AccountRef
    >>> chart_of_account = ChartOfAccountsRef(
    >>> id="chart_example",
    >>> code="code_example",
    >>> scope="scope_example")

    >>> account_ref = AccountRef(
    >>> id="account_example",
    >>> account_code="code_example",
    >>> chart_of_accounts=chart_of_account)
    """

    id: str = Field(exclude=True, init=True)
    account_code: str = Field(exclude=True, init=True)
    chart_of_accounts: ChartOfAccountsKey

    def attach(self, client):
        scope = self.chart_of_accounts.scope
        code = self.chart_of_accounts.code

        request_url = f"/api/api/chartofaccounts/{scope}/{code}/accounts/{self.account_code}"
        try:
            client.request("get", request_url)
        except httpx.HTTPStatusError as ex:
            if ex.response.status_code == 404:
                raise RuntimeError(f"Account {self.account_code} not found")
            else:
                raise ex


@register_resource()
class AccountResource(BaseModel, Resource):
    """Define an Account for Chart of Account in LUSID"""

    id: str = Field(exclude=True)
    chart_of_accounts: ChartOfAccountsKey
    code: str
    description: str | None = None
    type: AccountType
    status: AccountStatus
    control: Literal["System", "Manual"] | None = "Manual"
    properties: PropertyValueDict | None = None

    @model_validator(mode="before")
    @classmethod
    def des_model(cls, data, info) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return data
        # Handle id from context (for dump/undump)
        if info.context and info.context.get("id"):
            data = data | {"id": info.context.get("id")}
        return data

    def __get_content_hash__(self) -> str:
        dump = self.model_dump(mode="json", exclude_none=True, by_alias=True)
        return sha256(json.dumps(dump, sort_keys=True).encode()).hexdigest()

    def read(self, client: httpx.Client, old_state) -> None | Dict[str, Any]:
        scope = old_state.scope
        code = old_state.code
        account_code = old_state.account_code

        property_get = f"/api/api/chartofaccounts/{scope}/{code}/accounts/{account_code}/properties"
        properties = client.get(property_get).json()

        params = []
        if "properties" in properties:
            property_keys_list = []
            for key in properties["properties"]:
                property_keys_list.append(key)

            params = [("propertyKeys", prop_key) for prop_key in property_keys_list]

        request_url = f"/api/api/chartofaccounts/{scope}/{code}/accounts/{account_code}"
        return client.get(request_url, params=params).json()

    def create(self, client: httpx.Client) -> Optional[Dict[str, Any]]:
        desired = self.model_dump(
            mode="json",
            exclude_none=True,
            by_alias=True,
            exclude={"chart_of_accounts"})

        desired_wrap = [desired]
        scope = self.chart_of_accounts.scope
        code = self.chart_of_accounts.code

        request_url = f"/api/api/chartofaccounts/{scope}/{code}/accounts"
        response = client.post(request_url, json=desired_wrap).json()

        account_to_dump = response["accounts"][0]
        return {
            "account_code": self.code,
            "scope": scope,
            "code": code,
            "source_version": self.__get_content_hash__(),
            "remote_version": sha256(json.dumps(account_to_dump, sort_keys=True).encode()).hexdigest(),
        }

    def update(self, client: httpx.Client, old_state) -> Union[None, Dict[str, Any]]:
        scope = self.chart_of_accounts.scope
        code = self.chart_of_accounts.code

        if old_state.account_code != self.code:
            self.delete(client, old_state)
            return self.create(client)

        if old_state.code != code:
            raise (RuntimeError("Cannot change the code on an account"))

        if old_state.scope != scope:
            raise (RuntimeError("Cannot change the scope on an accounts"))

        source_hash = self.__get_content_hash__()
        remote = self.read(client, old_state)
        remote_hash = sha256(json.dumps(remote, sort_keys=True).encode()).hexdigest()

        if remote_hash == old_state.remote_version and source_hash == old_state.source_version:
            return None

        return self.create(client)

    @staticmethod
    def delete(client: httpx.Client, old_state) -> None:
        scope = old_state.scope
        code = old_state.code
        account = [old_state.account_code]
        client.post(f"/api/api/chartofaccounts/{scope}/{code}/accounts/$delete", json=account)

    def deps(self):
        deps = []
        deps.append(self.chart_of_accounts)
        deps += self.chart_of_accounts.deps()

        if self.properties is None:
            return deps

        for perp_prop in self.properties:
            deps.append(perp_prop.property_key)

        return deps


def ser_account_key(value, info):
    if info.context and info.context.get("style") == "dump":
        return {"$ref": value.id}
    return value.code


def des_account_key(value, info):
    if not isinstance(value, dict):
        return value
    if info.context and info.context.get("$refs"):
        ref = info.context["$refs"][value["$ref"]]
        return ref
    return value


AccountKey = Annotated[
    AccountRef | AccountResource,
    BeforeValidator(des_account_key), PlainSerializer(ser_account_key)
]
