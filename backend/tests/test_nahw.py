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


@pytest.mark.asyncio
async def test_nahw_annotation_model_fields_and_indexes(db_session: AsyncSession, seed_quran_data):
    annotation = NahwAnnotation(
        verse_id=1,
        word_id=1,
        token_index=5,
        role="مفعول به",
        dep_type="dobj",
        head_index=1,
        irab="منصوب",
        sentence_index=2,
    )
    db_session.add(annotation)
    await db_session.commit()
    await db_session.refresh(annotation)

    fetched = await db_session.get(NahwAnnotation, annotation.id)
    assert fetched is not None
    assert fetched.verse_id == 1
    assert fetched.word_id == 1
    assert fetched.token_index == 5
    assert fetched.role == "مفعول به"
    assert fetched.dep_type == "dobj"
    assert fetched.head_index == 1
    assert fetched.irab == "منصوب"
    assert fetched.sentence_index == 2
    assert fetched.created_at is not None
    assert fetched.updated_at is not None

    result = await db_session.execute(
        select(NahwAnnotation)
        .where(NahwAnnotation.verse_id == 1, NahwAnnotation.token_index == 5)
    )
    assert result.scalar_one().sentence_index == 2
