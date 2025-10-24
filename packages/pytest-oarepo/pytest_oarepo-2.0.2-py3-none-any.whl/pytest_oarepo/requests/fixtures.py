#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# oarepo-requests is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
"""Test fixtures for requests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Protocol

import pytest
from deepmerge import always_merger
from invenio_access.permissions import system_identity
from invenio_accounts.models import Role
from invenio_accounts.proxies import current_datastore
from invenio_records_permissions.generators import SystemProcess
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_requests.records.api import RequestEventFormat
from invenio_requests.services.generators import Receiver
from invenio_users_resources.proxies import current_groups_service

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask_principal import Identity
    from invenio_db.shared import SQLAlchemy
    from invenio_records_resources.services import RecordService
    from invenio_requests.services.requests import RequestItem
    from invenio_requests.services.requests.service import RequestsService
    from pytest_invenio.user import UserFixtureBase

can_comment_only_receiver = [
    Receiver(),
    SystemProcess(),
]


class CreateRequestFn(Protocol):
    """Callable to create a request on a topic record."""

    def __call__(  # noqa PLR0913
        self,
        identity: Identity,
        id_: str,
        request_type: str,
        topic_read_method: Literal["read", "read_draft"],
        additional_data: dict[str, Any] | None = ...,
        expand: bool = ...,
        **request_kwargs: Any,
    ) -> RequestItem:  # type: ignore[reportReturnType]
        """Create request of specific type on a specific record."""


class CreateRequestOnTopicFn(Protocol):
    """Callable to create a request on a record."""

    def __call__(
        self,
        identity: Identity,
        topic_id: str,
        request_type: str,
        additional_data: dict[str, Any] | None = ...,
        expand: bool = ...,
        **request_kwargs: Any,
    ) -> RequestItem:  # type: ignore[reportReturnType]
        """Create request of specific type on a specific record."""


class SubmitRequestFn(Protocol):
    """Callable to create and submit a request on a topic record."""

    def __call__(  # noqa PLR0913
        self,
        identity: Identity,
        topic_id: str,
        request_type: str,
        create_additional_data: dict[str, Any] | None = ...,
        submit_additional_data: dict[str, Any] | None = ...,
        expand: bool = ...,
    ) -> RequestItem:  # type: ignore[reportReturnType]
        """Create and submit request of specific type on a specific record."""


def _create_role(id_: str, name: str, description: str, is_managed: bool) -> Role:
    """Create a Role/Group."""
    r = current_datastore.create_role(id=id_, name=name, description=description, is_managed=is_managed)
    current_datastore.commit()
    return r


@pytest.fixture
def role() -> Role:
    """Create a Role/Group."""
    return _create_role(
        id_="it-dep",
        name="it-dep",
        description="IT Department",
        is_managed=False,
    )


@pytest.fixture
def add_user_in_role(db: SQLAlchemy) -> Callable[[UserFixtureBase, Role | str], None]:
    """Add user to role or creates it if it doesn't exist."""

    def _add_user_in_role(user: UserFixtureBase, role_or_role_name: Role | str) -> None:
        if isinstance(role_or_role_name, str):
            try:
                role = current_groups_service.read(system_identity, role_or_role_name)._group.model.model_obj  # noqa SLF001
            except PermissionDeniedError:  # missing group in db raises this
                role = Role(name=role_or_role_name)
                db.session.add(role_or_role_name)
        else:
            role = role_or_role_name
        # TODO: UserFixtureBase is not typed
        user.user.roles.append(role)  # type: ignore[reportOptionalMemberAccess]
        db.session.commit()

    return _add_user_in_role


@pytest.fixture
def role_ui_serialization(host: str) -> dict[str, Any]:
    """UI serialization of the example role in role fixture."""
    return {
        "label": "it-dep",
        "links": {
            "avatar": f"{host}api/groups/it-dep/avatar.svg",
            "self": f"{host}api/groups/it-dep",
        },
        "reference": {"group": "it-dep"},
        "type": "group",
    }


@pytest.fixture
def events_resource_data() -> dict[str, Any]:
    """Fixture for adding required input data default values for events."""
    return {
        "payload": {
            "content": "This is an event.",
            "format": RequestEventFormat.HTML.value,
        }
    }


@pytest.fixture
def request_type_additional_data() -> dict[str, Any]:
    """Fixture for adding required input data default values specific by request type."""
    return {"publish_draft": {"payload": {"version": "1.0"}}}


@pytest.fixture
def create_request(
    request_type_additional_data: dict[str, Any],
    record_service: RecordService,
    requests_service: RequestsService,
) -> CreateRequestFn:
    """Return base function for creating a request."""

    def _create_request(  # noqa PLR0913
        identity: Identity,
        id_: str,
        request_type: str,
        topic_read_method: str,
        additional_data: dict[str, Any] | None = None,
        expand: bool = False,
        **request_kwargs: Any,
    ) -> RequestItem:
        """Create request of specific type on a specific record.

        :param identity: Identity of the caller.
        :param id_: ID of the topic record.
        :param request_type: ID of the request type.
        :param topic_read_method: Method the service uses to read the topic.
        :param additional_data: Additional data needed to create the request.
        :param expand: Expand the created request response.
        :param service_kwargs: Additional keyword arguments to pass to request service.
        """
        topic_service = record_service
        if additional_data is None:
            additional_data = {}

        if request_type in request_type_additional_data:
            additional_data = always_merger.merge(additional_data, request_type_additional_data[request_type])

        topic = getattr(topic_service, topic_read_method)(system_identity, id_)._obj  # noqa SLF001
        return requests_service.create(
            identity,
            data=additional_data,
            request_type=request_type,
            topic=topic,
            expand=expand,
            **request_kwargs,
        )

    return _create_request


@pytest.fixture
def create_request_on_draft(
    create_request: CreateRequestFn,
) -> CreateRequestOnTopicFn:
    """Fixture for creating a request on a draft."""

    def _create(
        identity: Identity,
        topic_id: str,
        request_type: str,
        additional_data: dict[str, Any] | None = None,
        expand: bool = False,
        **request_kwargs: Any,
    ) -> RequestItem:
        """Create request of specific type on a draft record.

        :param identity: Identity of the caller.
        :param topic_id: ID of the topic record.
        :param request_type: Type of the request.
        :param additional_data: Additional data needed to create the request.
        :param expand: Expand the created request response.
        :param service_kwargs: Additional keyword arguments to pass to request service.
        """
        return create_request(
            identity,
            topic_id,
            request_type,
            topic_read_method="read_draft",
            additional_data=additional_data,
            expand=expand,
            **request_kwargs,
        )

    return _create


@pytest.fixture
def create_request_on_record(
    create_request: CreateRequestFn,
) -> CreateRequestOnTopicFn:
    """Fixture for creating a request on a published record."""

    def _create(
        identity: Identity,
        topic_id: str,
        request_type: str,
        additional_data: dict[str, Any] | None = None,
        expand: bool = False,
        **request_kwargs: Any,
    ) -> RequestItem:
        """Create request of specific type on a published record.

        :param identity: Identity of the caller.
        :param topic_id: ID of the topic record.
        :param request_type: Type of the request.
        :param additional_data: Additional data needed to create the request.
        :param expand: Expand the created request response.
        :param service_kwargs: Additional keyword arguments to pass to request service.
        """
        return create_request(
            identity,
            topic_id,
            request_type,
            topic_read_method="read",
            additional_data=additional_data,
            expand=expand,
            **request_kwargs,
        )

    return _create


@pytest.fixture
def submit_request_on_draft(
    create_request_on_draft: CreateRequestOnTopicFn,
    requests_service: RequestsService,
) -> SubmitRequestFn:
    """Fixture for creating and submitting request on a draft in one call."""

    def _submit_request(  # noqa PLR0913
        identity: Identity,
        topic_id: str,
        request_type: str,
        create_additional_data: dict[str, Any] | None = None,
        submit_additional_data: dict[str, Any] | None = None,
        expand: bool = False,
    ) -> RequestItem:
        """Create and submit request of specific type on a specific record.

        :param identity: Identity of tha caller.
        :param topic_id: ID of the topic record.
        :param request_type: Type of the request.
        :param create_additional_data: Additional data needed to create the request.
        :param submit_additional_data: Additional data passed to the submit action.
        :param expand: Expand the created request response.
        :param service_kwargs: Additional keyword arguments to pass to request service.
        """
        create_response = create_request_on_draft(
            identity, topic_id, request_type, additional_data=create_additional_data
        )
        return requests_service.execute_action(
            identity,
            id_=create_response["id"],
            action="submit",
            data=submit_additional_data,
            expand=expand,
        )

    return _submit_request


@pytest.fixture
def submit_request_on_record(
    create_request_on_record: CreateRequestOnTopicFn,
    requests_service: RequestsService,
) -> SubmitRequestFn:
    """Fixture for creating and submitting request on a published record in one call."""

    def _submit_request(  # noqa PLR0913
        identity: Identity,
        topic_id: str,
        request_type: str,
        create_additional_data: dict[str, Any] | None = None,
        submit_additional_data: dict[str, Any] | None = None,
        expand: bool = False,
    ) -> RequestItem:
        """Create and submit request of specific type on a specific record.

        :param client: Client instance.
        :param record: Record on which the request should be created.
        :param request_type: Which type of request should be created.
        :param create_additional_data: Additional data needed to create the request.
        :param submit_additional_data: Additional data passed to the submit action.
        :param expand: Expand the submitted request response.
        """
        create_response = create_request_on_record(
            identity, topic_id, request_type, additional_data=create_additional_data
        )
        return requests_service.execute_action(
            identity,
            id_=create_response["id"],
            action="submit",
            data=submit_additional_data,
            expand=expand,
        )

    return _submit_request
