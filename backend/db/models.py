from datetime import datetime, timezone
from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def utcnow():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    scenario: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200), default="")
    users: Mapped[int]
    seed: Mapped[int]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ReportRow(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("runs.id"))
    device_id: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(8))
    t: Mapped[float]
    cell11: Mapped[str] = mapped_column(String(16))
    cell10: Mapped[str] = mapped_column(String(16))
    cell8: Mapped[str] = mapped_column(String(16))
    source: Mapped[str] = mapped_column(String(8))
    text: Mapped[str | None] = mapped_column(String(280))
    __table_args__ = (Index("ix_reports_run_t", "run_id", "t"), Index("ix_reports_cell_cat", "cell8", "category"))

class IncidentRow(Base):
    __tablename__ = "incidents"
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("runs.id"), primary_key=True)
    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    category: Mapped[str] = mapped_column(String(16))
    max_level: Mapped[int]
    status: Mapped[str] = mapped_column(String(12))
    confidence: Mapped[str] = mapped_column(String(12))
    district: Mapped[str] = mapped_column(String(64))
    devices: Mapped[int]
    first_t: Mapped[float | None]
    data: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(primary_key=True)
    street: Mapped[str] = mapped_column(String(120))
    place: Mapped[str] = mapped_column(String(120))
    housenumber: Mapped[str] = mapped_column(String(24))
    key: Mapped[str] = mapped_column(String(200), index=True)
    lat: Mapped[float]
    lng: Mapped[float]
    cell10: Mapped[str] = mapped_column(String(16))

class Facility(Base):
    __tablename__ = "facilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(32), index=True)
    address: Mapped[str] = mapped_column(String(200))
    district_id: Mapped[int | None]
    cell8: Mapped[str] = mapped_column(String(16), index=True)
    cell11: Mapped[str] = mapped_column(String(16))
    lat: Mapped[float]
    lng: Mapped[float]

class ResolvedIssue(Base):
    __tablename__ = "resolved_landscape_issues"
    
    issue_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50))

    description: Mapped[str | None] = mapped_column(String(4000))
    resolution_notes: Mapped[str | None] = mapped_column(String(4000))
    
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)