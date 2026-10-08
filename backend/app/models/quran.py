from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Surah(TimestampMixin, Base):
    __tablename__ = "surahs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name_arabic: Mapped[str] = mapped_column(String(100), nullable=False)
    name_transliteration: Mapped[str] = mapped_column(String(100), nullable=False)
    name_english: Mapped[str] = mapped_column(String(100), nullable=False)
    revelation_place: Mapped[str | None] = mapped_column(String(10), nullable=True)
    verse_count: Mapped[int] = mapped_column(Integer, nullable=False)

    verses: Mapped[list[Verse]] = relationship(
        back_populates="surah", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Surah {self.number} {self.name_english!r}>"


class Verse(TimestampMixin, Base):
    __tablename__ = "verses"
    __table_args__ = (UniqueConstraint("surah_id", "ayah_number", name="uq_verse_surah_ayah"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    surah_id: Mapped[int] = mapped_column(ForeignKey("surahs.id"), nullable=False, index=True)
    ayah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text_uthmani: Mapped[str] = mapped_column(Text, nullable=False)
    text_imlaei: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_ur: Mapped[str | None] = mapped_column(Text, nullable=True)
    juz_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hizb_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    surah: Mapped[Surah] = relationship(back_populates="verses")
    words: Mapped[list[Word]] = relationship(back_populates="verse", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Verse {self.surah_id}:{self.ayah_number}>"


class Word(TimestampMixin, Base):
    __tablename__ = "words"
    __table_args__ = (UniqueConstraint("verse_id", "position", name="uq_word_verse_pos"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(ForeignKey("verses.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    text_uthmani: Mapped[str] = mapped_column(Text, nullable=False)
    text_imlaei: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    transliteration: Mapped[str | None] = mapped_column(Text, nullable=True)
    root: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    lemma: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    pos_tag: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tense: Mapped[str | None] = mapped_column(String(30), nullable=True)
    voice: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    person: Mapped[str | None] = mapped_column(String(20), nullable=True)
    features_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    verse: Mapped[Verse] = relationship(back_populates="words")

    def __repr__(self) -> str:
        return f"<Word {self.verse_id}:{self.position} {self.text_uthmani!r}>"


class NahwAnnotation(TimestampMixin, Base):
    __tablename__ = "nahw_annotations"
    __table_args__ = (
        UniqueConstraint("verse_id", "token_index", name="uq_nahw_verse_token"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    verse_id: Mapped[int] = mapped_column(
        ForeignKey("verses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_id: Mapped[int | None] = mapped_column(
        ForeignKey("words.id", ondelete="SET NULL"), nullable=True, index=True
    )
    token_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dep_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    head_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    irab: Mapped[str | None] = mapped_column(String(50), nullable=True)

    verse: Mapped[Verse] = relationship()
    word: Mapped[Word | None] = relationship()

    def __repr__(self) -> str:
        return f"<NahwAnnotation {self.verse_id}:{self.token_index} {self.role!r}>"
