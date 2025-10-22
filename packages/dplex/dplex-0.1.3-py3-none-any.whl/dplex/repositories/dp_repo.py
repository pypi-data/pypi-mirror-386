import uuid
from typing import Any, Generic

from sqlalchemy import select, func, and_, delete, ColumnElement, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from dplex.repositories.query_builder import QueryBuilder
from dplex.types import ModelType, KeyType


class DPRepo(Generic[ModelType, KeyType]):
    """Базовый репозиторий с улучшенной типизацией"""

    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
        key_type: type[KeyType] = uuid.UUID,
        id_field_name: str = "id",
    ) -> None:
        self.model = model
        self.session = session
        self.key_type = key_type
        self.id_field_name = id_field_name
        self._id_column = self._get_id_column()

    def _get_id_column(self) -> InstrumentedAttribute[KeyType]:
        """Получить типизированную ID колонку"""
        if not hasattr(self.model, self.id_field_name):
            raise ValueError(
                f"Model {self.model.__name__} does not have field '{self.id_field_name}'"
            )

        column = getattr(self.model, self.id_field_name)

        # Проверяем что это SQLAlchemy column
        if not hasattr(column, "property"):
            raise ValueError(
                f"Field '{self.id_field_name}' in {self.model.__name__} is not a SQLAlchemy column"
            )

        return column

    def query(self) -> "QueryBuilder[ModelType]":
        """Создать типизированный query builder"""
        return QueryBuilder(self, self.model)

    def id_eq(self, value: KeyType) -> ColumnElement[bool]:
        """Возвращает условие для сравнения ID с entity_id"""
        return self._id_column == value

    def id_in(self, values: list[KeyType]) -> ColumnElement[bool]:
        """Возвращает условие для проверки ID в списке значений"""
        return self._id_column.in_(values)

    # Методы с использованием закешированной колонки
    async def find_by_id(self, entity_id: KeyType) -> ModelType | None:
        """Найти сущность по ID"""
        return await self.query().where(self.id_eq(entity_id)).find_one()

    async def find_by_ids(self, entity_ids: list[KeyType]) -> list[ModelType]:
        """Найти сущности по списку ID"""
        return await self.query().where(self.id_in(entity_ids)).find_all()

    async def delete_by_query_builder(
        self,
        query_builder: "QueryBuilder[ModelType]",
    ) -> None:
        """
        Массовое удаление по условиям из QueryBuilder.
        Использует централизованную логику построения WHERE.
        """
        condition = self._build_where_clause_from_builder(query_builder)
        if condition is None:
            raise ValueError(
                "DPRepo.delete_by_query_builder: требуется хотя бы одно условие WHERE для массового удаления"
            )

        stmt = delete(self.model).where(condition)
        await self.session.execute(stmt)

    async def delete_by_id(self, entity_id: KeyType) -> None:
        """Удалить сущность по ID"""
        stmt = delete(self.model).where(self.id_eq(entity_id))
        await self.session.execute(stmt)

    async def delete_by_ids(self, entity_ids: list[KeyType]) -> None:
        """Удалить сущности по ID"""
        stmt = delete(self.model).where(self.id_in(entity_ids))
        await self.session.execute(stmt)

    async def update(
        self,
        where: ColumnElement[bool] | list[ColumnElement[bool]] | None,
        values: dict[str, Any],
    ) -> None:
        """
        Универсальный UPDATE по условию(ям).
        """
        if not values:
            return None
        if where is None:
            raise ValueError("DPRepo.update: пустой WHERE запрещён")

        condition: ColumnElement[bool]
        if isinstance(where, list):
            if not where:
                raise ValueError("DPRepo.update: пустой список условий WHERE запрещён")
            condition = and_(*where)
        else:
            condition = where

        stmt = update(self.model).where(condition).values(**values)
        await self.session.execute(stmt)

    async def update_by_query_builder(
        self,
        query_builder: "QueryBuilder[ModelType]",
        values: dict[str, Any],
    ) -> None:
        # ...
        if not values:
            return None

        condition = self._build_where_clause_from_builder(query_builder)
        if condition is None:
            raise ValueError(
                "DPRepo.update_by_query_builder: требуется хотя бы одно условие WHERE"
            )

        stmt = update(self.model).where(condition).values(**values)
        await self.session.execute(stmt)

    async def update_by_id(self, entity_id: KeyType, values: dict[str, Any]) -> None:
        """Обновить сущность по ID"""
        stmt = update(self.model).where(self.id_eq(entity_id)).values(**values)
        await self.session.execute(stmt)

    async def update_by_ids(
        self, entity_ids: list[KeyType], values: dict[str, Any]
    ) -> None:
        """Обновить сущности по ID"""
        stmt = update(self.model).where(self.id_in(entity_ids)).values(**values)
        await self.session.execute(stmt)

    async def exists_by_id(self, entity_id: KeyType) -> bool:
        """Проверить существование сущности по ID"""
        count = await self.query().where(self.id_eq(entity_id)).count()
        return count > 0

    async def create(self, entity: ModelType) -> ModelType:
        """Создать новую сущность"""
        self.session.add(entity)
        return entity

    async def create_bulk(self, entities: list[ModelType]) -> list[ModelType]:
        """Создать несколько сущностей"""
        self.session.add_all(entities)
        return entities

    async def commit(self) -> None:
        """Сохранить изменения в базе данных"""
        await self.session.commit()

    async def rollback(self) -> None:
        """Откатить изменения"""
        await self.session.rollback()

    @staticmethod
    def _build_where_clause_from_builder(
        builder: "QueryBuilder[ModelType]",
    ) -> ColumnElement[bool] | None:
        """
        Строит единое WHERE условие из фильтров QueryBuilder'а.
        Возвращает None, если фильтров нет.
        """
        if builder.filters:
            return and_(*builder.filters)
        return None

    # Методы для выполнения запросов билдера
    async def execute_typed_query(
        self, builder: "QueryBuilder[ModelType]"
    ) -> list[ModelType]:
        """Выполнить типизированный запрос"""
        stmt = select(self.model)

        condition = self._build_where_clause_from_builder(builder)
        if condition is not None:
            stmt = stmt.where(condition)

        if builder.order_by_clauses:
            stmt = stmt.order_by(*builder.order_by_clauses)

        if builder.limit_value is not None:
            stmt = stmt.limit(builder.limit_value)

        if builder.offset_value is not None:
            stmt = stmt.offset(builder.offset_value)

        result = await self.session.scalars(stmt)
        return list(result.all())

    async def execute_typed_count(self, builder: "QueryBuilder[ModelType]") -> int:
        """Подсчитать записи через типизированный билдер"""
        stmt = select(func.count()).select_from(self.model)

        # Используем новый хелпер
        condition = self._build_where_clause_from_builder(builder)
        if condition is not None:
            stmt = stmt.where(condition)

        result = await self.session.execute(stmt)
        return result.scalar_one()
