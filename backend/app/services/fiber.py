from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.models.enums import AuditEventType
from app.models.fiber import OLT, ONU, PON, OpticalThreshold
from app.repositories.fiber import FiberRepository, OpticalThresholdRepository
from app.repositories.metrics import MetricRepository
from app.schemas.fiber import (
    ONUOpticalHistoryResponse,
    ONUOpticalMetric,
    ONUOpticalStatusResponse,
    OpticalClassification,
    OpticalHistoryPoint,
    OpticalHistoryWindow,
    OpticalThresholdCreate,
    OpticalThresholdUpdate,
)
from app.schemas.metrics import MetricEntityType, MetricQuery, MetricResolution
from app.services.audit import AuditService

CURRENT_METRICS = {
    "RX_POWER": ("rx_power", "dBm"),
    "TX_POWER": ("tx_power", "dBm"),
    "TEMPERATURE": ("temperature", "celsius"),
    "DISTANCE": ("distance", "meters"),
}
HISTORY_WINDOWS = {
    OpticalHistoryWindow.HOURS_24: (timedelta(hours=24), MetricResolution.FIVE_MINUTES),
    OpticalHistoryWindow.DAYS_7: (timedelta(days=7), MetricResolution.HOURLY),
    OpticalHistoryWindow.DAYS_30: (timedelta(days=30), MetricResolution.DAILY),
}


class FiberService:
    def __init__(
        self,
        repository: FiberRepository,
        thresholds: OpticalThresholdRepository,
        metrics: MetricRepository,
    ) -> None:
        self.repository = repository
        self.thresholds = thresholds
        self.metrics = metrics

    async def list_olts(self) -> list[OLT]:
        return await self.repository.list_olts()

    async def get_olt(self, olt_id: UUID) -> OLT:
        olt = await self.repository.get_olt(olt_id)
        if olt is None:
            raise AppError("OLT_NOT_FOUND", "OLT not found.", 404)
        return olt

    async def list_pons(
        self, *, olt_id: UUID | None = None, status: str | None = None
    ) -> list[PON]:
        return await self.repository.list_pons(olt_id=olt_id, status=_clean(status))

    async def get_pon(self, pon_id: UUID) -> PON:
        pon = await self.repository.get_pon(pon_id)
        if pon is None:
            raise AppError("PON_NOT_FOUND", "PON not found.", 404)
        return pon

    async def list_onus(
        self,
        *,
        olt_id: UUID | None = None,
        pon_id: UUID | None = None,
        subscriber_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[ONU]:
        return await self.repository.list_onus(
            olt_id=olt_id,
            pon_id=pon_id,
            subscriber_id=_clean(subscriber_id),
            status=_clean(status),
            search=_clean(search),
            offset=offset,
            limit=limit,
        )

    async def get_onu(self, onu_id: UUID) -> ONU:
        onu = await self.repository.get_onu(onu_id)
        if onu is None:
            raise AppError("ONU_NOT_FOUND", "ONU not found.", 404)
        return onu

    async def optical_status(self, onu_id: UUID) -> ONUOpticalStatusResponse:
        context = await self._context(onu_id)
        onu, pon, olt = context
        thresholds = await self._threshold_map(olt, pon)
        metrics = [
            ONUOpticalMetric(
                metric_name=name,
                value=getattr(onu, attribute),
                unit=unit,
                classification=classify(getattr(onu, attribute), thresholds.get(name)),
            )
            for name, (attribute, unit) in CURRENT_METRICS.items()
        ]
        return ONUOpticalStatusResponse(
            onu_id=onu.id,
            observed_at=onu.last_seen,
            metrics=metrics,
        )

    async def optical_history(
        self, onu_id: UUID, window: OpticalHistoryWindow
    ) -> ONUOpticalHistoryResponse:
        onu = await self.get_onu(onu_id)
        if window == OpticalHistoryWindow.CURRENT:
            points = [
                OpticalHistoryPoint(
                    timestamp=onu.last_seen or datetime.now(UTC),
                    metric_name=name,
                    value=value,
                    value_min=value,
                    value_max=value,
                    unit=unit,
                )
                for name, (attribute, unit) in CURRENT_METRICS.items()
                if (value := getattr(onu, attribute)) is not None
            ]
            return ONUOpticalHistoryResponse(
                onu_id=onu.id,
                window=window,
                resolution="current",
                points=points,
            )
        duration, resolution = HISTORY_WINDOWS[window]
        end = datetime.now(UTC)
        rows = await self.metrics.query_aggregate(
            MetricQuery(
                start=end - duration,
                end=end,
                entity_type=MetricEntityType.ONU,
                entity_id=onu.onu_identifier,
                resolution=resolution,
                limit=10_000,
            )
        )
        allowed_names = {
            "rx_optical_power",
            "tx_optical_power",
            "temperature",
            "voltage",
            "distance",
        }
        points = [
            OpticalHistoryPoint(
                timestamp=row["bucket"],
                metric_name=row["metric_name"],
                value=row["value_avg"],
                value_min=row["value_min"],
                value_max=row["value_max"],
                unit=row["unit"],
            )
            for row in rows
            if row["metric_name"] in allowed_names
        ]
        return ONUOpticalHistoryResponse(
            onu_id=onu.id,
            window=window,
            resolution=resolution.value,
            points=points,
        )

    async def _context(self, onu_id: UUID) -> tuple[ONU, PON, OLT]:
        context = await self.repository.get_onu_context(onu_id)
        if context is None:
            raise AppError("ONU_NOT_FOUND", "ONU not found.", 404)
        return context

    async def _threshold_map(
        self, olt: OLT, pon: PON
    ) -> dict[str, OpticalThreshold]:
        matches = await self.thresholds.matching(
            vendor=olt.vendor,
            technology=pon.technology,
            device_model=olt.model,
        )
        return {threshold.metric_name: threshold for threshold in matches}


class OpticalThresholdService:
    def __init__(
        self,
        repository: OpticalThresholdRepository,
        audit: AuditService,
    ) -> None:
        self.repository = repository
        self.audit = audit

    async def list(self) -> list[OpticalThreshold]:
        return await self.repository.list_thresholds()

    async def create(
        self, payload: OpticalThresholdCreate, actor_user_id: UUID
    ) -> OpticalThreshold:
        try:
            threshold = await self.repository.add(
                OpticalThreshold(**payload.model_dump(mode="python"))
            )
            await self._audit(threshold.id, "created", actor_user_id)
            await self.repository.session.commit()
            return threshold
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError(
                "OPTICAL_THRESHOLD_CONFLICT",
                "An optical threshold already exists for this scope and metric.",
                409,
            ) from exc

    async def update(
        self,
        threshold_id: UUID,
        payload: OpticalThresholdUpdate,
        actor_user_id: UUID,
    ) -> OpticalThreshold:
        threshold = await self._get(threshold_id)
        values = {
            field: getattr(threshold, field)
            for field in OpticalThresholdCreate.model_fields
        }
        values.update(payload.model_dump(exclude_unset=True))
        validated = OpticalThresholdCreate.model_validate(values)
        try:
            for field, value in validated.model_dump(mode="python").items():
                setattr(threshold, field, value)
            await self.repository.session.flush()
            await self._audit(threshold.id, "updated", actor_user_id)
            await self.repository.session.commit()
            return threshold
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise AppError(
                "OPTICAL_THRESHOLD_CONFLICT",
                "An optical threshold already exists for this scope and metric.",
                409,
            ) from exc

    async def delete(self, threshold_id: UUID, actor_user_id: UUID) -> None:
        threshold = await self._get(threshold_id)
        await self.repository.delete(threshold)
        await self._audit(threshold.id, "deleted", actor_user_id)
        await self.repository.session.commit()

    async def _get(self, threshold_id: UUID) -> OpticalThreshold:
        threshold = await self.repository.get(threshold_id)
        if threshold is None:
            raise AppError(
                "OPTICAL_THRESHOLD_NOT_FOUND",
                "Optical threshold not found.",
                404,
            )
        return threshold

    async def _audit(
        self, threshold_id: UUID, action: str, actor_user_id: UUID
    ) -> None:
        await self.audit.record(
            AuditEventType.THRESHOLD_CHANGED,
            success=True,
            actor_user_id=actor_user_id,
            event_metadata={
                "resource_type": "OpticalThreshold",
                "resource_id": str(threshold_id),
                "action": action,
            },
        )


def classify(
    value: float | None, threshold: OpticalThreshold | None
) -> OpticalClassification:
    if value is None or threshold is None:
        return OpticalClassification.UNKNOWN
    if (
        threshold.critical_low is not None
        and value <= threshold.critical_low
    ) or (
        threshold.critical_high is not None
        and value >= threshold.critical_high
    ):
        return OpticalClassification.CRITICAL
    if (
        threshold.warning_low is not None
        and value <= threshold.warning_low
    ) or (
        threshold.warning_high is not None
        and value >= threshold.warning_high
    ):
        return OpticalClassification.WARNING
    return OpticalClassification.GOOD


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
