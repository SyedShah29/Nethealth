from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import OutageCorrelation, RootCauseAssessment


class AnalysisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_correlation(self, item: OutageCorrelation) -> OutageCorrelation:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_correlation(self, item_id: UUID) -> OutageCorrelation | None:
        return await self.session.get(OutageCorrelation, item_id)

    async def list_correlations(self, limit: int = 100) -> list[OutageCorrelation]:
        result = await self.session.execute(
            select(OutageCorrelation)
            .order_by(OutageCorrelation.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def add_assessment(self, item: RootCauseAssessment) -> RootCauseAssessment:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_assessment(self, item_id: UUID) -> RootCauseAssessment | None:
        return await self.session.get(RootCauseAssessment, item_id)

    async def list_assessments(self, limit: int = 100) -> list[RootCauseAssessment]:
        result = await self.session.execute(
            select(RootCauseAssessment)
            .order_by(RootCauseAssessment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())
