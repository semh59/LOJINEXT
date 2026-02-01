"""
TIR Yakıt Takip - Base Repository
SQLAlchemy ORM tabanlı güvenli versiyon.
"""

from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, func, insert, inspect, select, text, update as sql_update

import contextlib
from sqlalchemy.ext.asyncio import AsyncSession
import app.database.connection as conn
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository using SQLAlchemy ORM.
    Tüm işlemler ORM modelleri üzerinden yapılır (SQL Injection Safe).
    """

    model: Type[T] = None  # Alt sınıfta tanımlanmalı (örn: model = Arac)

    def __init__(self, session: Optional[AsyncSession] = None):
        if self.model is None:
            raise ValueError(f"Model attribute must be set in {self.__class__.__name__}")
        self.session = session

    @contextlib.asynccontextmanager
    async def _get_session(self):
        """Session yönetimini merkezileştirir."""
        if self.session:
            yield self.session
        else:
            async with conn.AsyncSessionLocal() as session:
                yield session

    def _to_dict(self, obj: T) -> Dict[str, Any]:
        """ORM objesini dictionary'e çevirir"""
        if obj is None:
            return None
        return {c.key: getattr(obj, c.key) for c in inspect(self.model).mapper.column_attrs}

    # Pagination & Search Security
    MAX_LIMIT = 1000
    search_columns: List[str] = []

    async def get_all(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = 100,
        offset: int = 0,
        include_inactive: bool = False
    ) -> List[Dict]:
        """Tüm kayıtları getir (ORM)."""
        limit = max(1, min(int(limit), self.MAX_LIMIT))
        offset = max(0, int(offset))

        stmt = select(self.model)

        if hasattr(self.model, 'aktif') and not include_inactive:
            stmt = stmt.where(self.model.aktif == True)

        if filters:
            from sqlalchemy import or_
            _filters = filters.copy()
            
            # Handle standardized search
            search_query = _filters.pop("search", None)
            if search_query and self.search_columns:
                search_filters = []
                for col in self.search_columns:
                    if hasattr(self.model, col):
                        search_filters.append(getattr(self.model, col).ilike(f"%{search_query}%"))
                if search_filters:
                    stmt = stmt.where(or_(*search_filters))

            # Handle regular equality and range filters
            for k, v in _filters.items():
                if v is None: continue
                
                # Range filters
                if k.endswith("_ge"):
                    real_k = k[:-3]
                    if hasattr(self.model, real_k):
                        stmt = stmt.where(getattr(self.model, real_k) >= v)
                elif k.endswith("_le"):
                    real_k = k[:-3]
                    if hasattr(self.model, real_k):
                        stmt = stmt.where(getattr(self.model, real_k) <= v)
                # Equality filters
                elif hasattr(self.model, k):
                    stmt = stmt.where(getattr(self.model, k) == v)

        if order_by:
            parts = order_by.split()
            col_name = parts[0]
            direction = parts[1].lower() if len(parts) > 1 else "asc"

            if hasattr(self.model, col_name):
                col = getattr(self.model, col_name)
                if direction == "desc":
                    stmt = stmt.order_by(col.desc())
                else:
                    stmt = stmt.order_by(col.asc())
        else:
             pk = inspect(self.model).primary_key[0]
             stmt = stmt.order_by(pk.desc())

        stmt = stmt.limit(limit).offset(offset)

        async with self._get_session() as session:
            result = await session.execute(stmt)
            objs = result.scalars().all()
            return [self._to_dict(obj) for obj in objs]

    async def get_by_id(self, id: int, for_update: bool = False) -> Optional[Dict]:
        """ID ile kayıt getir."""
        async with self._get_session() as session:
            if for_update:
                stmt = select(self.model).where(inspect(self.model).primary_key[0] == id).with_for_update()
                result = await session.execute(stmt)
                obj = result.scalar_one_or_none()
            else:
                obj = await session.get(self.model, id)
            return self._to_dict(obj)

    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[Any]:
        """Toplu kayıt oluştur."""
        if not data_list:
            return []

        async with self._get_session() as session:
            try:
                physical_columns = {c.name for c in self.model.__table__.columns}
                objs = []
                for data in data_list:
                    filtered_data = {k: v for k, v in data.items() if k in physical_columns}
                    objs.append(self.model(**filtered_data))
                
                session.add_all(objs)
                
                if not self.session:
                    await session.commit()
                else:
                    await session.flush()
                
                # Fetch IDs (obj.id logic)
                return [getattr(obj, inspect(self.model).primary_key[0].name) for obj in objs]
            except Exception as e:
                if not self.session:
                    await session.rollback()
                logger.error(f"Bulk create error for {self.model.__name__}: {e}")
                raise e

    async def create(self, **data) -> Any:
        """Yeni kayıt oluştur (En güvenli ve ilkel yöntem)"""
        async with self._get_session() as session:
            try:
                # SADECE fiziksel kolonları metadata üzerinden filtrele
                physical_columns = {c.name for c in self.model.__table__.columns}
                filtered_data = {k: v for k, v in data.items() if k in physical_columns}

                # [INJECTION] Eğer created_at kolonu varsa ve veride yoksa, otomatik ekle
                if "created_at" in physical_columns and "created_at" not in filtered_data:
                    from datetime import datetime
                    filtered_data["created_at"] = datetime.now()

                # RETURNING olmadan insertion (En geniş SQLite uyumu için)
                stmt = insert(self.model).values(**filtered_data)
                result = await session.execute(stmt)
                
                # Fetch ID (SQLite inserted_primary_key support)
                new_id = result.inserted_primary_key[0]
                
                if not self.session:
                    await session.commit()
                
                logger.debug(f"Created {self.model.__tablename__} record id={new_id}")
                return new_id
            except Exception as e:
                if not self.session:
                    await session.rollback()
                logger.error(f"Create error for {self.model.__name__}: {e}")
                raise e
    async def update(self, id: int, **data) -> bool:
        """Kayıt güncelle"""
        if not data:
            return False

        pk_attr = inspect(self.model).primary_key[0].name
        if pk_attr in data:
            del data[pk_attr]

        async with self._get_session() as session:
            try:
                # Filter data
                physical_columns = {c.name for c in self.model.__table__.columns}
                filtered_data = {k: v for k, v in data.items() if k in physical_columns}

                if not filtered_data:
                    return False

                stmt = sql_update(self.model).where(getattr(self.model, pk_attr) == id).values(**filtered_data)
                result = await session.execute(stmt)
                
                if not self.session:
                    await session.commit()
                return result.rowcount > 0
            except Exception as e:
                if not self.session:
                    await session.rollback()
                logger.error(f"Update error for {self.model.__name__}: {e}")
                raise e

    async def delete(self, id: int) -> bool:
        """Kayıt sil."""
        if hasattr(self.model, 'aktif'):
            return await self.update(id, aktif=False)
        else:
            return await self.hard_delete(id)

    async def hard_delete(self, id: int) -> bool:
        """Kalıcı silme"""
        pk = inspect(self.model).primary_key[0]
        async with self._get_session() as session:
            try:
                stmt = delete(self.model).where(pk == id)
                result = await session.execute(stmt)
                if not self.session:
                    await session.commit()
                return result.rowcount > 0
            except Exception as e:
                if not self.session:
                    await session.rollback()
                raise e

    async def exists(self, id: int) -> bool:
        pk = inspect(self.model).primary_key[0]
        stmt = select(1).where(pk == id).limit(1)
        async with self._get_session() as session:
            result = await session.execute(stmt)
            return result.scalar() is not None

    async def count(self, filters: Dict[str, Any] = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        if filters:
            for k, v in filters.items():
                if hasattr(self.model, k) and v is not None:
                    stmt = stmt.where(getattr(self.model, k) == v)
        async with self._get_session() as session:
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def execute_query(self, query: str, params: dict = None) -> List[Dict]:
        """Custom Raw SQL support."""
        async with self._get_session() as session:
            try:
                result = await session.execute(text(query), params or {})
                return [dict(row) for row in result.mappings().all()]
            except Exception as e:
                logger.error(f"Database query error: {e}")
                if not self.session: await session.rollback()
                raise e

    async def execute_scalar(self, query: str, params: dict = None) -> Any:
        async with self._get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.scalar()
