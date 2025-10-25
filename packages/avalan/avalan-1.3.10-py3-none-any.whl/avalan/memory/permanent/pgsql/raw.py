from ....memory.partitioner.text import TextPartition
from ....memory.permanent import (
    Entity,
    Hyperedge,
    Memory,
    MemoryType,
    PermanentMemory,
    PermanentMemoryPartition,
    VectorFunction,
)
from ....memory.permanent.pgsql import PgsqlMemory

from dataclasses import dataclass
from datetime import datetime, timezone
from json import dumps
from logging import Logger
from uuid import UUID, uuid4

from pgvector.psycopg import Vector


class PgsqlRawMemory(PgsqlMemory[Memory], PermanentMemory):
    @classmethod
    async def create_instance(
        cls,
        dsn: str,
        *args,
        logger: Logger,
        pool_minimum: int = 1,
        pool_maximum: int = 10,
        pool_open: bool = True,
        **kwargs,
    ):
        memory = cls(
            dsn=dsn,
            logger=logger,
            pool_minimum=pool_minimum,
            pool_maximum=pool_maximum,
            **kwargs,
        )
        if pool_open:
            await memory.open()
        return memory

    async def append_with_partitions(
        self,
        namespace: str,
        participant_id: UUID,
        *args,
        memory_type: MemoryType,
        data: str,
        identifier: str,
        partitions: list[TextPartition],
        symbols: dict | None = None,
        model_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> None:
        assert (
            namespace and participant_id and data and identifier and partitions
        )
        now_utc = datetime.now(timezone.utc)
        entry, partition_rows = self._build_memory_with_partitions(
            namespace,
            participant_id,
            memory_type,
            data,
            identifier,
            partitions,
            created_at=now_utc,
            symbols=symbols,
            model_id=model_id,
            memory_id=uuid4(),
            title=title,
            description=description,
        )

        async with self._database.connection() as connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO "memories"(
                            "id",
                            "model_id",
                            "participant_id",
                            "memory_type",
                            "namespace",
                            "identifier",
                            "data",
                            "partitions",
                            "symbols",
                            "created_at",
                            "title",
                            "description"
                        ) VALUES (
                            %s, %s, %s, %s::memory_types,
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            str(entry.id),
                            entry.model_id,
                            str(entry.participant_id),
                            str(entry.type),
                            entry.namespace,
                            entry.identifier,
                            entry.data,
                            entry.partitions,
                            (
                                dumps(entry.symbols)
                                if entry.symbols is not None
                                else None
                            ),
                            entry.created_at,
                            entry.title,
                            entry.description,
                        ),
                    )

                    await cursor.executemany(
                        """
                        INSERT INTO "memory_partitions"(
                            "participant_id",
                            "memory_id",
                            "partition",
                            "data",
                            "embedding",
                            "created_at"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s
                        )
                        """,
                        [
                            (
                                str(mp.participant_id),
                                str(mp.memory_id),
                                mp.partition,
                                mp.data,
                                Vector(mp.embedding),
                                mp.created_at,
                            )
                            for mp in partition_rows
                        ],
                    )
                    await cursor.close()

    @dataclass(frozen=True, kw_only=True, slots=True)
    class _MemoryRow:
        id: UUID
        model_id: str | None
        memory_type: str
        participant_id: UUID
        namespace: str
        identifier: str
        partitions: int
        symbols: dict | None
        created_at: datetime
        title: str | None
        description: str | None

    async def list_memories(
        self,
        *,
        participant_id: UUID,
        namespace: str,
    ) -> list[Memory]:
        assert participant_id and namespace
        records = await self._fetch_all(
            self._MemoryRow,
            """
            SELECT
                "id",
                "model_id",
                "memory_type",
                "participant_id",
                "namespace",
                "identifier",
                "partitions",
                "symbols",
                "created_at",
                "title",
                "description"
            FROM "memories"
            WHERE "participant_id" = %s
              AND "namespace" = %s
              AND "is_deleted" = FALSE
            ORDER BY "created_at" DESC
            """,
            (str(participant_id), namespace),
        )
        memories: list[Memory] = []
        for record in records:
            memory_type = (
                record.memory_type
                if isinstance(record.memory_type, MemoryType)
                else MemoryType(record.memory_type)
            )
            memories.append(
                Memory(
                    id=record.id,
                    model_id=record.model_id,
                    type=memory_type,
                    participant_id=record.participant_id,
                    namespace=record.namespace,
                    identifier=record.identifier,
                    data=None,
                    partitions=record.partitions,
                    symbols=record.symbols,
                    created_at=record.created_at,
                    title=record.title,
                    description=record.description,
                )
            )
        return memories

    async def search_memories(
        self,
        *args,
        search_partitions: list[TextPartition],
        participant_id: UUID,
        namespace: str,
        function: VectorFunction,
        limit: int | None = None,
    ) -> list[PermanentMemoryPartition]:
        assert participant_id and namespace and search_partitions
        search_function = str(function)
        search_vector = Vector(search_partitions[0].embeddings)
        limit_value = limit or 10
        partitions = await self._fetch_all(
            PermanentMemoryPartition,
            f"""
            SELECT
                "memory_partitions"."participant_id",
                "memory_partitions"."memory_id",
                "memory_partitions"."partition",
                "memory_partitions"."data",
                "memory_partitions"."embedding",
                "memory_partitions"."created_at"
            FROM "memory_partitions"
            INNER JOIN "memories" ON (
                "memory_partitions"."memory_id" = "memories"."id"
            )
            WHERE "memories"."participant_id" = %s
            AND "memories"."namespace" = %s
            AND "memories"."is_deleted" = FALSE
            ORDER BY {search_function}(
                "memory_partitions"."embedding",
                %s
            ) ASC
            LIMIT %s
            """,
            (
                str(participant_id),
                namespace,
                search_vector,
                limit_value,
            ),
        )
        return partitions

    async def upsert_hyperedge(
        self,
        hyperedge: Hyperedge,
        *,
        memory_id: UUID,
        char_start: int | None = None,
        char_end: int | None = None,
    ) -> None:
        assert hyperedge and memory_id
        async with self._database.connection() as connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO "hyperedges"(
                            "id",
                            "relation",
                            "surface_text",
                            "embedding",
                            "symbols",
                            "created_at"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT ("id") DO UPDATE SET
                            "relation" = EXCLUDED."relation",
                            "surface_text" = EXCLUDED."surface_text",
                            "embedding" = EXCLUDED."embedding",
                            "symbols" = EXCLUDED."symbols"
                        """,
                        (
                            str(hyperedge.id),
                            hyperedge.relation,
                            hyperedge.surface_text,
                            Vector(hyperedge.embedding),
                            (
                                dumps(hyperedge.symbols)
                                if hyperedge.symbols is not None
                                else None
                            ),
                            hyperedge.created_at,
                        ),
                    )

                    await cursor.execute(
                        """
                        INSERT INTO "hyperedges_memories"(
                            "hyperedge_id",
                            "memory_id",
                            "char_start",
                            "char_end"
                        ) VALUES (
                            %s, %s, %s, %s
                        )
                        ON CONFLICT ("hyperedge_id", "memory_id") DO UPDATE SET
                            "char_start" = EXCLUDED."char_start",
                            "char_end" = EXCLUDED."char_end"
                        """,
                        (
                            str(hyperedge.id),
                            str(memory_id),
                            char_start,
                            char_end,
                        ),
                    )
                    await cursor.close()

    async def upsert_entity(
        self,
        entity: Entity,
        *,
        hyperedge_id: UUID,
        role_idx: int,
        role_label: str | None = None,
    ) -> UUID:
        assert entity and hyperedge_id and role_idx >= 1
        async with self._database.connection() as connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO "entities"(
                            "id",
                            "name",
                            "type",
                            "embedding",
                            "symbols",
                            "participant_id",
                            "namespace",
                            "created_at"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT ON CONSTRAINT "uq_entities_scope_name"
                        DO UPDATE SET
                            "type" = EXCLUDED."type",
                            "embedding" = EXCLUDED."embedding",
                            "symbols" = EXCLUDED."symbols"
                        RETURNING "id"
                        """,
                        (
                            str(entity.id),
                            entity.name,
                            entity.type,
                            Vector(entity.embedding),
                            (
                                dumps(entity.symbols)
                                if entity.symbols is not None
                                else None
                            ),
                            (
                                str(entity.participant_id)
                                if entity.participant_id
                                else None
                            ),
                            entity.namespace,
                            entity.created_at,
                        ),
                    )
                    result = await cursor.fetchone()
                    entity_id = result["id"] if result else None

                    await cursor.execute(
                        """
                        INSERT INTO "hyperedge_entities"(
                            "hyperedge_id",
                            "entity_id",
                            "role_idx",
                            "role_label"
                        ) VALUES (
                            %s, %s, %s, %s
                        )
                        ON CONFLICT ("hyperedge_id", "role_idx") DO UPDATE SET
                            "entity_id" = EXCLUDED."entity_id",
                            "role_label" = EXCLUDED."role_label"
                        """,
                        (
                            str(hyperedge_id),
                            str(entity_id),
                            role_idx,
                            role_label,
                        ),
                    )
                    await cursor.close()
        return UUID(entity_id) if isinstance(entity_id, str) else entity_id
