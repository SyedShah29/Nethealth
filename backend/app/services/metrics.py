from datetime import datetime
from typing import Any

from app.collectors.schemas import (
    DeviceHealth,
    EnvironmentReading,
    InterfaceHealth,
    OpticalMetric,
)
from app.models.inventory import Interface
from app.repositories.metrics import MetricRepository
from app.schemas.metrics import (
    MetricEntityType,
    MetricQuery,
    MetricResolution,
    MetricSampleCreate,
)


class MetricService:
    def __init__(self, repository: MetricRepository) -> None:
        self.repository = repository

    async def query(self, query: MetricQuery) -> list[Any]:
        if query.resolution == MetricResolution.RAW:
            return await self.repository.query_raw(query)
        return await self.repository.query_aggregate(query)

    async def persist_collection(
        self,
        *,
        timestamp: datetime,
        source: str,
        health: DeviceHealth,
        interfaces: list[InterfaceHealth],
        inventory_interfaces: dict[str, Interface],
        optical: list[OpticalMetric],
        environment: list[EnvironmentReading],
        subscriber_sessions: list[dict[str, object]],
    ) -> list[MetricSampleCreate]:
        samples = self._device_samples(timestamp, source, health, environment)
        for reading in interfaces:
            interface = inventory_interfaces.get(reading.name)
            entity_id = (
                str(interface.id)
                if interface is not None
                else f"{health.device_id}:{reading.name}"
            )
            samples.extend(
                await self._interface_samples(
                    timestamp, source, entity_id, reading, interface.speed if interface else None
                )
            )
        samples.extend(
            self._optical_samples(
                timestamp, source, health.device_id, optical, inventory_interfaces
            )
        )
        samples.extend(self._subscriber_samples(timestamp, source, subscriber_sessions))
        await self.repository.add_many(samples)
        return samples

    @staticmethod
    def _sample(
        timestamp: datetime,
        entity_type: MetricEntityType,
        entity_id: str,
        name: str,
        value: float | int | bool | None,
        unit: str | None,
        source: str,
        tags: dict[str, str] | None = None,
    ) -> MetricSampleCreate | None:
        if value is None:
            return None
        return MetricSampleCreate(
            timestamp=timestamp,
            entity_type=entity_type,
            entity_id=entity_id,
            metric_name=name,
            value=float(value),
            unit=unit,
            source=source,
            tags=tags or {},
        )

    def _device_samples(
        self,
        timestamp: datetime,
        source: str,
        health: DeviceHealth,
        environment: list[EnvironmentReading],
    ) -> list[MetricSampleCreate]:
        values: dict[str, tuple[float | int | bool | None, str | None]] = {
            "cpu_percent": (health.cpu_percent, "%"),
            "memory_percent": (health.memory_percent, "%"),
            "uptime_seconds": (health.uptime_seconds, "seconds"),
            "reachability": (health.reachable, "boolean"),
            "latency_ms": (health.latency_ms, "ms"),
            "packet_loss_percent": (health.packet_loss_percent, "%"),
        }
        for reading in environment:
            name = (
                f"{reading.metric}_percent"
                if reading.metric in {"cpu", "memory"}
                else reading.metric
            )
            values.setdefault(name, (reading.value, reading.unit))
        return [
            sample
            for name, (value, unit) in values.items()
            if (sample := self._sample(
                timestamp,
                MetricEntityType.DEVICE,
                str(health.device_id),
                name,
                value,
                unit,
                source,
            ))
            is not None
        ]

    async def _interface_samples(
        self,
        timestamp: datetime,
        source: str,
        entity_id: str,
        reading: InterfaceHealth,
        speed_bps: int | None,
    ) -> list[MetricSampleCreate]:
        samples: list[MetricSampleCreate] = []
        state_value = {"UP": 1.0, "DOWN": 0.0}.get(reading.oper_status or "", -1.0)
        state = self._sample(
            timestamp,
            MetricEntityType.INTERFACE,
            entity_id,
            "operational_state",
            state_value,
            "state",
            source,
            {"state": reading.oper_status or "UNKNOWN", "interface_name": reading.name},
        )
        if state is not None:
            samples.append(state)
        for name, value in (("errors", reading.errors), ("discards", reading.discards)):
            sample = self._sample(
                timestamp, MetricEntityType.INTERFACE, entity_id, name, value, "count", source
            )
            if sample is not None:
                samples.append(sample)
        counters = (("inbound", reading.in_octets), ("outbound", reading.out_octets))
        for direction, counter in counters:
            counter_name = f"{direction}_octets_total"
            counter_sample = self._sample(
                timestamp,
                MetricEntityType.INTERFACE,
                entity_id,
                counter_name,
                counter,
                "octets",
                source,
            )
            if counter_sample is not None:
                samples.append(counter_sample)
            if counter is None:
                continue
            previous = await self.repository.latest_value(
                MetricEntityType.INTERFACE.value, entity_id, counter_name, timestamp
            )
            if previous is None or counter < previous.value:
                continue
            elapsed = (timestamp - previous.timestamp).total_seconds()
            if elapsed <= 0:
                continue
            bits_per_second = (counter - previous.value) * 8 / elapsed
            rate = self._sample(
                timestamp,
                MetricEntityType.INTERFACE,
                entity_id,
                f"{direction}_bps",
                bits_per_second,
                "bps",
                source,
            )
            if rate is not None:
                samples.append(rate)
            if speed_bps and speed_bps > 0:
                utilization = self._sample(
                    timestamp,
                    MetricEntityType.INTERFACE,
                    entity_id,
                    f"{direction}_utilization_percent",
                    min(100.0, bits_per_second / speed_bps * 100),
                    "%",
                    source,
                )
                if utilization is not None:
                    samples.append(utilization)
        return samples

    def _optical_samples(
        self,
        timestamp: datetime,
        source: str,
        device_id: object,
        readings: list[OpticalMetric],
        interfaces: dict[str, Interface],
    ) -> list[MetricSampleCreate]:
        samples: list[MetricSampleCreate] = []
        for reading in readings:
            entity_type = MetricEntityType(reading.entity_type)
            entity_id = reading.entity_id
            if entity_id is None:
                interface = interfaces.get(reading.interface_name)
                entity_id = (
                    str(interface.id)
                    if interface
                    else f"{device_id}:{reading.interface_name}"
                )
            sample = self._sample(
                timestamp,
                entity_type,
                entity_id,
                reading.metric,
                reading.value,
                reading.unit,
                source,
                {"interface_name": reading.interface_name},
            )
            if sample is not None:
                samples.append(sample)
        return samples

    def _subscriber_samples(
        self,
        timestamp: datetime,
        source: str,
        sessions: list[dict[str, object]],
    ) -> list[MetricSampleCreate]:
        names = {
            "session_state": "state",
            "session_uptime": "seconds",
            "download_rate": "bps",
            "upload_rate": "bps",
            "disconnect_events": "count",
        }
        samples: list[MetricSampleCreate] = []
        for session in sessions:
            entity_id = session.get("subscriber_id")
            if not isinstance(entity_id, str) or not entity_id:
                continue
            for name, unit in names.items():
                value = session.get(name)
                tags: dict[str, str] = {}
                if name == "session_state" and isinstance(value, str):
                    tags["state"] = value
                    value = 1 if value.upper() == "ONLINE" else 0
                if not isinstance(value, int | float | bool):
                    continue
                sample = self._sample(
                    timestamp,
                    MetricEntityType.SUBSCRIBER,
                    entity_id,
                    name,
                    value,
                    unit,
                    source,
                    tags,
                )
                if sample is not None:
                    samples.append(sample)
        return samples
