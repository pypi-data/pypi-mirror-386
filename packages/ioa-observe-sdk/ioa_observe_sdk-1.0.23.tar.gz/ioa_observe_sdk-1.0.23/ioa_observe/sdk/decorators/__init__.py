# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import inspect
from typing import Optional, Union, TypeVar, Callable, Any

from typing_extensions import ParamSpec

from ioa_observe.sdk.decorators.base import (
    entity_class,
    entity_method,
)
from ioa_observe.sdk.utils.const import ObserveSpanKindValues


P = ParamSpec("P")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


def task(
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    protocol: Optional[str] = None,
    application_id: Optional[str] = None,
    method_name: Optional[str] = None,
    tlp_span_kind: Optional[ObserveSpanKindValues] = ObserveSpanKindValues.TASK,
) -> Callable[[F], F]:
    if method_name is None:
        return entity_method(
            name=name,
            description=description,
            version=version,
            protocol=protocol,
            application_id=application_id,
            tlp_span_kind=tlp_span_kind,
        )
    else:
        return entity_class(
            name=name,
            description=description,
            version=version,
            protocol=protocol,
            application_id=application_id,
            method_name=method_name,
            tlp_span_kind=tlp_span_kind,
        )


def workflow(
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    protocol: Optional[str] = None,
    application_id: Optional[str] = None,
    method_name: Optional[str] = None,
    tlp_span_kind: Optional[
        Union[ObserveSpanKindValues, str]
    ] = ObserveSpanKindValues.WORKFLOW,
) -> Callable[[F], F]:
    def decorator(target):
        # Check if target is a class
        if inspect.isclass(target):
            return entity_class(
                name=name,
                description=description,
                version=version,
                protocol=protocol,
                application_id=application_id,
                method_name=method_name,
                tlp_span_kind=tlp_span_kind,
            )(target)
        else:
            # Target is a function/method
            return entity_method(
                name=name,
                description=description,
                version=version,
                protocol=protocol,
                application_id=application_id,
                tlp_span_kind=tlp_span_kind,
            )(target)

    return decorator


def graph(
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    application_id: Optional[str] = None,
    method_name: Optional[str] = None,
    protocol: Optional[str] = None,
) -> Callable[[F], F]:
    if method_name is None:
        return entity_method(
            name=name,
            description=description,
            version=version,
            protocol=protocol,
            application_id=application_id,
            tlp_span_kind="graph",
        )
    else:
        return entity_class(
            name=name,
            description=description,
            version=version,
            method_name=method_name,
            protocol=protocol,
            application_id=application_id,
            tlp_span_kind="graph",
        )


def agent(
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    protocol: Optional[str] = None,
    application_id: Optional[str] = None,
    method_name: Optional[str] = None,
) -> Callable[[F], F]:
    return workflow(
        name=name,
        description=description,
        version=version,
        protocol=protocol,
        application_id=application_id,
        method_name=method_name,
        tlp_span_kind=ObserveSpanKindValues.AGENT,
    )


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[int] = None,
    application_id: Optional[str] = None,
    method_name: Optional[str] = None,
) -> Callable[[F], F]:
    return task(
        name=name,
        description=description,
        version=version,
        application_id=application_id,
        method_name=method_name,
        tlp_span_kind=ObserveSpanKindValues.TOOL,
    )
