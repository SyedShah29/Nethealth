from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.fiber import OLT, ONU, PON, OpticalThreshold


class FiberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_olts(self) -> list[OLT]:
        result = await self.session.execute(select(OLT).order_by(OLT.vendor, OLT.model))
        return list(result.scalars().all())

    async def get_olt(self, olt_id: UUID) -> OLT | None:
        return await self.session.get(OLT, olt_id)

    async def list_pons(
        self, *, olt_id: UUID | None = None, status: str | None = None
    ) -> list[PON]:
        statement = select(PON)
        if olt_id is not None:
            statement = statement.where(PON.olt_id == olt_id)
        if status is not None:
            statement = statement.where(PON.status == status)
        result = await self.session.execute(
            statement.order_by(PON.olt_id, PON.frame, PON.slot, PON.port)
        )
        return list(result.scalars().all())

    async def get_pon(self, pon_id: UUID) -> PON | None:
        return await self.session.get(PON, pon_id)

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
        statement = select(ONU)
        for column, value in (
            (ONU.olt_id, olt_id),
            (ONU.pon_id, pon_id),
            (ONU.subscriber_id, subscriber_id),
            (ONU.status, status),
        ):
            if value is not None:
                statement = statement.where(column == value)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    ONU.onu_identifier.ilike(pattern),
                    ONU.serial_number.ilike(pattern),
                    ONU.subscriber_id.ilike(pattern),
                )
            )
        result = await self.session.execute(
            statement.order_by(ONU.onu_identifier).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get_onu(self, onu_id: UUID) -> ONU | None:
        return await self.session.get(ONU, onu_id)

    async def get_onu_context(self, onu_id: UUID) -> tuple[ONU, PON, OLT] | None:
        row = (
            await self.session.execute(
                select(ONU, PON, OLT)
                .join(PON, PON.id == ONU.pon_id)
                .join(OLT, OLT.id == PON.olt_id)
                .where(ONU.id == onu_id)
            )
        ).one_or_none()
        if row is None:
            return None
        onu, pon, olt = row
        return onu, pon, olt


class OpticalThresholdRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_thresholds(self) -> list[OpticalThreshold]:
        result = await self.session.execute(
            select(OpticalThreshold).order_by(
                OpticalThreshold.vendor,
                OpticalThreshold.technology,
                OpticalThreshold.device_model,
                OpticalThreshold.metric_name,
            )
        )
        return list(result.scalars().all())

    async def get(self, threshold_id: UUID) -> OpticalThreshold | None:
        return await self.session.get(OpticalThreshold, threshold_id)

    async def matching(
        self, *, vendor: str, technology: str, device_model: str
    ) -> list[OpticalThreshold]:
        result = await self.session.execute(
            select(OpticalThreshold)
            .where(
                func.upper(OpticalThreshold.vendor) == vendor.upper(),
                func.upper(OpticalThreshold.technology) == technology.upper(),
                or_(
                    OpticalThreshold.device_model.is_(None),
                    func.upper(OpticalThreshold.device_model) == device_model.upper(),
                ),
            )
            .order_by(OpticalThreshold.device_model.asc().nulls_first())
        )
        return list(result.scalars().all())

    async def add(self, threshold: OpticalThreshold) -> OpticalThreshold:
        self.session.add(threshold)
        await self.session.flush()
        return threshold

    async def delete(self, threshold: OpticalThreshold) -> None:
        await self.session.delete(threshold)
        await self.session.flush()
