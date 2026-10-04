from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import NahwAnnotation


@pytest.mark.asyncio
async def test_insert_and_read_nahw_annotation(db_session: AsyncSession, seed_quran_data):
    annotation = NahwAnnotation(
        verse_id=1,
        word_id=None,
        token_index=1,
        role="مبتدأ",
        dep_type="mubtada",
        head_index=2,
        irab="رفع",
    )
    db_session.add(annotation)
    await db_session.commit()

    result = await db_session.execute(
        select(NahwAnnotation).where(NahwAnnotation.verse_id == 1)
    )
    fetched = result.scalar_one()
    assert fetched.token_index == 1
    assert fetched.role == "مبتدأ"
    assert fetched.dep_type == "mubtada"
    assert fetched.head_index == 2
    assert fetched.irab == "رفع"
    assert fetched.word_id is None
