from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
class User(Base):
    __tablename__="users"; id:Mapped[int]=mapped_column(Integer, primary_key=True); username:Mapped[str]=mapped_column(String(128), unique=True, nullable=False); password_hash:Mapped[str]=mapped_column(String(255), nullable=False); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, nullable=False)
class Favorite(Base):
    __tablename__="favorites"; __table_args__=(UniqueConstraint("path", name="uq_favorites_path"),); id:Mapped[int]=mapped_column(Integer, primary_key=True); path:Mapped[str]=mapped_column(Text, nullable=False); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, nullable=False)
class RecentPath(Base):
    __tablename__="recent_paths"; __table_args__=(UniqueConstraint("path", name="uq_recent_path"),); id:Mapped[int]=mapped_column(Integer, primary_key=True); path:Mapped[str]=mapped_column(Text, nullable=False); last_accessed_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, nullable=False)
class Preference(Base):
    __tablename__="preferences"; key:Mapped[str]=mapped_column(String(128), primary_key=True); value:Mapped[str]=mapped_column(Text, nullable=False)
class OperationLog(Base):
    __tablename__="operation_logs"; id:Mapped[int]=mapped_column(Integer, primary_key=True); action:Mapped[str]=mapped_column(String(64), nullable=False); source_path:Mapped[str|None]=mapped_column(Text); target_path:Mapped[str|None]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, nullable=False)
class TrashRecord(Base):
    __tablename__="trash_records"; id:Mapped[int]=mapped_column(Integer, primary_key=True); original_path:Mapped[str]=mapped_column(Text, nullable=False); trash_path:Mapped[str]=mapped_column(Text, nullable=False); original_name:Mapped[str]=mapped_column(Text, nullable=False); deleted_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, nullable=False)
