from ....entities import EngineMessage, EngineMessageScored
from ....memory.partitioner.text import TextPartition
from ....memory.permanent import (
    PermanentMessage,
    PermanentMessageMemory,
    PermanentMessageScored,
    VectorFunction,
)
from ....memory.permanent.pgsql import PgsqlMemory

from datetime import datetime, timezone
from logging import Logger
from uuid import UUID, uuid4

from pgvector.psycopg import Vector


class PgsqlMessageMemory(
    PgsqlMemory[PermanentMessage], PermanentMessageMemory
):
    """PostgreSQL-backed implementation of :class:`PermanentMessageMemory`."""

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
        """Create a memory store backed by a PostgreSQL connection."""
        memory = cls(
            dsn=dsn,
            composite_types=["message_author_type"],
            logger=logger,
            pool_minimum=pool_minimum,
            pool_maximum=pool_maximum,
            **kwargs,
        )
        if pool_open:
            await memory.open()
        return memory

    async def create_session(
        self, *args, agent_id: UUID, participant_id: UUID
    ) -> UUID:
        """Create a new session for a participant."""
        now_utc = datetime.now(timezone.utc)
        session = self._build_session(
            agent_id,
            participant_id,
            created_at=now_utc,
        )
        async with self._database.connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO "sessions"(
                        "id",
                        "agent_id",
                        "participant_id",
                        "messages",
                        "created_at"
                    ) VALUES (
                        %s, %s, %s, %s, %s
                    )
                """,
                    (
                        str(session.id),
                        str(session.agent_id),
                        str(session.participant_id),
                        session.messages,
                        session.created_at,
                    ),
                )
                await cursor.close()
        return session.id

    async def continue_session_and_get_id(
        self,
        *args,
        agent_id: UUID,
        participant_id: UUID,
        session_id: UUID,
    ) -> UUID:
        """Continue an existing session if it belongs to the participant."""
        session_id = await self._fetch_field(
            "id",
            """
            SELECT "sessions"."id"
            FROM "sessions"
            WHERE "agent_id" = %s
            AND "participant_id" = %s
            AND "id" = %s
            LIMIT 1
        """,
            (str(agent_id), str(participant_id), str(session_id)),
        )
        assert session_id
        return session_id if isinstance(session_id, UUID) else UUID(session_id)

    async def append_with_partitions(
        self,
        engine_message: EngineMessage,
        *args,
        partitions: list[TextPartition],
    ) -> None:
        """Persist a message and its partitions."""
        assert engine_message and partitions
        now_utc = datetime.now(timezone.utc)
        message, message_partitions = self._build_message_with_partitions(
            engine_message,
            self._session_id,
            partitions,
            created_at=now_utc,
            message_id=uuid4(),
        )

        async with self._database.connection() as connection:
            async with connection.transaction():
                async with connection.cursor() as cursor:
                    await cursor.execute(
                        """
                        INSERT INTO "messages"(
                            "id",
                            "agent_id",
                            "model_id",
                            "session_id",
                            "author",
                            "data",
                            "partitions",
                            "created_at"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """,
                        (
                            str(message.id),
                            str(message.agent_id),
                            str(message.model_id),
                            (
                                str(message.session_id)
                                if message.session_id
                                else None
                            ),
                            str(message.author),
                            message.data,
                            message.partitions,
                            message.created_at,
                        ),
                    )

                    if message.session_id:
                        await cursor.execute(
                            """
                            UPDATE "sessions"
                            SET "messages" = "messages" + 1
                            WHERE "id" = %s
                        """,
                            (str(message.session_id),),
                        )

                    await cursor.executemany(
                        """
                        INSERT INTO "message_partitions"(
                            "agent_id",
                            "session_id",
                            "message_id",
                            "partition",
                            "data",
                            "embedding",
                            "created_at"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s
                        )
                    """,
                        [
                            (
                                str(mp.agent_id),
                                str(mp.session_id) if mp.session_id else None,
                                str(mp.message_id),
                                mp.partition,
                                mp.data,
                                Vector(mp.embedding),
                                mp.created_at,
                            )
                            for mp in message_partitions
                        ],
                    )

                    await cursor.close()

    async def get_recent_messages(
        self,
        session_id: UUID,
        participant_id: UUID,
        *args,
        limit: int | None = None,
    ) -> list[EngineMessage]:
        """Retrieve recent messages for a session."""
        limit_value = limit or 10
        messages = await self._fetch_all(
            PermanentMessage,
            """
            SELECT
                "messages"."id",
                "messages"."agent_id",
                "messages"."model_id",
                "messages"."session_id",
                "messages"."author",
                "messages"."data",
                "messages"."partitions",
                "messages"."created_at"
            FROM "sessions"
            INNER JOIN "messages" ON "sessions"."id" = "messages"."session_id"
            WHERE "sessions"."id" = %s
            AND "sessions"."participant_id" = %s
            AND "messages"."is_deleted" = FALSE
            ORDER BY "messages"."created_at" DESC
            LIMIT %s
        """,
            (str(session_id), str(participant_id), limit_value),
        )
        engine_messages = self._to_engine_messages(
            messages, limit=limit_value, reverse=True
        )
        return engine_messages

    async def search_messages(
        self,
        *args,
        agent_id: UUID,
        function: VectorFunction,
        limit: int | None = None,
        participant_id: UUID,
        search_partitions: list[TextPartition],
        search_user_messages: bool,
        session_id: UUID | None,
        exclude_session_id: UUID | None,
    ) -> list[EngineMessageScored]:
        """Search messages using a similarity function."""
        assert agent_id and participant_id and search_partitions
        search_function = str(function)
        search_vector = Vector(search_partitions[0].embeddings)
        limit_value = limit or 10
        messages = await self._fetch_all(
            PermanentMessageScored,
            f"""
            SELECT
                "messages"."id",
                "messages"."agent_id",
                "messages"."model_id",
                "messages"."session_id",
                "messages"."author",
                "messages"."data",
                "messages"."partitions",
                "messages"."created_at",
                {search_function}(
                    "message_partitions"."embedding",
                    %s
                ) AS "score"
            FROM "sessions"
            INNER JOIN "message_partitions" ON (
                "sessions"."id" = "message_partitions"."session_id"
            )
            INNER JOIN "messages" ON (
                "message_partitions"."message_id" = "messages"."id"
            )
            WHERE "sessions"."participant_id" = %s
            AND "sessions"."agent_id" = %s
            AND "messages"."is_deleted" = FALSE
            AND "messages"."author" = (
                CASE WHEN %s THEN 'user'::message_author_type
                ELSE "messages"."author"
                END
            )
            AND "sessions"."id" = COALESCE(%s, "sessions"."id")
            AND "sessions"."id" != COALESCE(%s::UUID, NULL)
            ORDER BY "score" ASC
            LIMIT %s
        """,
            (
                search_vector,
                str(participant_id),
                str(agent_id),
                search_user_messages,
                str(session_id) if session_id else None,
                str(exclude_session_id) if exclude_session_id else None,
                limit_value,
            ),
        )
        engine_messages = self._to_engine_messages(
            messages,
            limit=limit_value,
            scored=True,
        )
        return engine_messages
