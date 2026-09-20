from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.dependencies.auth import get_current_user, get_subscriber_service
from app.core.errors import AppError
from app.main import create_app
from app.models.enums import PermissionCode, RoleName
from app.models.subscriber import Subscriber, SubscriberSession
from app.repositories.subscriber import SubscriberRepository
from app.schemas.subscriber import (
    SubscriberRecord,
    SubscriberResponse,
    SubscriberSessionRecord,
)
from app.services.subscriber import SubscriberService
from tests.factories import make_role, make_user


def _subscriber(subscriber_id: str = "SUB-10482") -> Subscriber:
    now = datetime.now(UTC)
    return Subscriber(
        subscriber_id=subscriber_id,
        external_reference="ISP-7781",
        package_speed=100_000_000,
        status="ACTIVE",
        nas_id="NAS-01",
        olt_id="OLT-07",
        pon_id="0/3/4",
        onu_id="ONU-139",
        current_ip="198.51.100.12",
        mac_address="02:00:00:00:00:01",
        created_at=now,
        updated_at=now,
    )


class FakeSubscriberRepository:
    def __init__(self, subscriber: Subscriber | None = None) -> None:
        self.subscriber = subscriber
        self.list_arguments: dict[str, Any] = {}
        self.sessions = [
            SubscriberSession(
                id=uuid4(),
                subscriber_id=subscriber.subscriber_id if subscriber else "SUB-10482",
                session_start=datetime.now(UTC),
                nas="NAS-01",
            )
        ]

    async def list_subscribers(self, **kwargs: Any) -> list[Subscriber]:
        self.list_arguments = kwargs
        return [self.subscriber] if self.subscriber else []

    async def get(self, _subscriber_id: str) -> Subscriber | None:
        return self.subscriber

    async def get_by_external_reference(self, _value: str) -> Subscriber | None:
        return self.subscriber

    async def list_sessions(
        self, _subscriber_id: str, *, limit: int
    ) -> list[SubscriberSession]:
        return self.sessions[:limit]


def _service(repository: FakeSubscriberRepository) -> SubscriberService:
    return SubscriberService(cast(SubscriberRepository, repository))


def test_subscriber_record_normalizes_operational_identifiers() -> None:
    record = SubscriberRecord(
        subscriber_id=" SUB-10482 ",
        external_reference=" ISP-7781 ",
        package_speed=100_000_000,
        current_ip="2001:db8::1",
        mac_address="02-00-00-00-00-01",
    )
    assert record.subscriber_id == "SUB-10482"
    assert record.external_reference == "ISP-7781"
    assert record.status == "UNKNOWN"
    assert record.current_ip == "2001:db8::1"
    assert record.mac_address == "02:00:00:00:00:01"


def test_subscriber_record_rejects_non_operational_identifier() -> None:
    with pytest.raises(ValidationError):
        SubscriberRecord(subscriber_id="Customer Full Name")


def test_session_record_calculates_duration_and_rejects_reverse_time() -> None:
    start = datetime.now(UTC)
    session = SubscriberSessionRecord(
        subscriber_id="SUB-10482",
        session_start=start,
        session_end=start + timedelta(seconds=90),
        nas="NAS-01",
    )
    assert session.duration == 90
    with pytest.raises(ValidationError):
        SubscriberSessionRecord(
            subscriber_id="SUB-10482",
            session_start=start,
            session_end=start - timedelta(seconds=1),
            nas="NAS-01",
        )


def test_subscriber_response_contains_no_prohibited_pii_fields() -> None:
    prohibited = {
        "cnic",
        "payment_details",
        "banking_information",
        "browsing_history",
        "dns_history",
        "home_address",
    }
    assert prohibited.isdisjoint(SubscriberResponse.model_fields)


async def test_subscriber_service_searches_and_resolves_external_mapping() -> None:
    repository = FakeSubscriberRepository(_subscriber())
    service = _service(repository)
    results = await service.list_subscribers(
        search=" SUB-10 ", status=" ACTIVE ", limit=25
    )
    resolved = await service.resolve_external_reference(" ISP-7781 ")
    assert results[0].subscriber_id == "SUB-10482"
    assert repository.list_arguments["search"] == "SUB-10"
    assert repository.list_arguments["status"] == "ACTIVE"
    assert resolved.subscriber_id == "SUB-10482"


async def test_subscriber_service_returns_standard_not_found_error() -> None:
    with pytest.raises(AppError) as error:
        await _service(FakeSubscriberRepository()).get_subscriber("SUB-MISSING")
    assert error.value.code == "SUBSCRIBER_NOT_FOUND"
    assert error.value.status_code == 404


async def test_subscriber_api_enforces_rbac_and_returns_records() -> None:
    app = create_app()
    subscriber = _subscriber()
    fake_service = SimpleNamespace(
        list_subscribers=lambda **_kwargs: _async_result([subscriber]),
    )
    app.dependency_overrides[get_current_user] = lambda: make_user(
        role=make_role(
            RoleName.SUPPORT,
            permissions=(PermissionCode.SUBSCRIBERS_READ,),
        )
    )
    app.dependency_overrides[get_subscriber_service] = lambda: fake_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/subscribers", params={"status": "ACTIVE"})
    assert response.status_code == 200
    assert response.json()[0]["subscriber_id"] == "SUB-10482"


async def test_subscriber_api_rejects_missing_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/subscribers")
    assert response.status_code == 401


async def _async_result(value: Any) -> Any:
    return value
