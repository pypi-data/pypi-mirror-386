import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from uuid import uuid4

from agno.db.async_postgres.schemas import get_table_schema_definition
from agno.db.async_postgres.utils import (
    apply_sorting,
    bulk_upsert_metrics,
    calculate_date_metrics,
    create_schema,
    deserialize_cultural_knowledge,
    fetch_all_sessions_data,
    get_dates_to_calculate_metrics_for,
    is_table_available,
    is_valid_table,
    serialize_cultural_knowledge,
)
from agno.db.base import AsyncBaseDb, SessionType
from agno.db.schemas.culture import CulturalKnowledge
from agno.db.schemas.evals import EvalFilterType, EvalRunRecord, EvalType
from agno.db.schemas.knowledge import KnowledgeRow
from agno.db.schemas.memory import UserMemory
from agno.session import AgentSession, Session, TeamSession, WorkflowSession
from agno.utils.log import log_debug, log_error, log_info, log_warning

try:
    from sqlalchemy import Index, String, UniqueConstraint, func, update
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
    from sqlalchemy.schema import Column, MetaData, Table
    from sqlalchemy.sql.expression import select, text
except ImportError:
    raise ImportError("`sqlalchemy` not installed. Please install it using `pip install sqlalchemy`")


class AsyncPostgresDb(AsyncBaseDb):
    def __init__(
        self,
        db_id: Optional[str] = None,
        db_url: Optional[str] = None,
        db_engine: Optional[AsyncEngine] = None,
        db_schema: Optional[str] = None,
        session_table: Optional[str] = None,
        memory_table: Optional[str] = None,
        metrics_table: Optional[str] = None,
        eval_table: Optional[str] = None,
        knowledge_table: Optional[str] = None,
        culture_table: Optional[str] = None,
    ):
        """
        Async interface for interacting with a PostgreSQL database.

        The following order is used to determine the database connection:
            1. Use the db_engine if provided
            2. Use the db_url
            3. Raise an error if neither is provided

        Args:
            db_id (Optional[str]): The ID of the database.
            db_url (Optional[str]): The database URL to connect to.
            db_engine (Optional[AsyncEngine]): The SQLAlchemy async database engine to use.
            db_schema (Optional[str]): The database schema to use.
            session_table (Optional[str]): Name of the table to store Agent, Team and Workflow sessions.
            memory_table (Optional[str]): Name of the table to store memories.
            metrics_table (Optional[str]): Name of the table to store metrics.
            eval_table (Optional[str]): Name of the table to store evaluation runs data.
            knowledge_table (Optional[str]): Name of the table to store knowledge content.
            culture_table (Optional[str]): Name of the table to store cultural knowledge.

        Raises:
            ValueError: If neither db_url nor db_engine is provided.
            ValueError: If none of the tables are provided.
        """
        super().__init__(
            id=db_id,
            session_table=session_table,
            memory_table=memory_table,
            metrics_table=metrics_table,
            eval_table=eval_table,
            knowledge_table=knowledge_table,
            culture_table=culture_table,
        )

        _engine: Optional[AsyncEngine] = db_engine
        if _engine is None and db_url is not None:
            _engine = create_async_engine(db_url)
        if _engine is None:
            raise ValueError("One of db_url or db_engine must be provided")

        self.db_url: Optional[str] = db_url
        self.db_engine: AsyncEngine = _engine
        self.db_schema: str = db_schema if db_schema is not None else "ai"
        self.metadata: MetaData = MetaData()

        # Initialize database session factory
        self.async_session_factory = async_sessionmaker(bind=self.db_engine)

    # -- DB methods --
    async def _create_table(self, table_name: str, table_type: str, db_schema: str) -> Table:
        """
        Create a table with the appropriate schema based on the table type.

        Args:
            table_name (str): Name of the table to create
            table_type (str): Type of table (used to get schema definition)
            db_schema (str): Database schema name

        Returns:
            Table: SQLAlchemy Table object
        """
        try:
            table_schema = get_table_schema_definition(table_type).copy()

            columns: List[Column] = []
            indexes: List[str] = []
            unique_constraints: List[str] = []
            schema_unique_constraints = table_schema.pop("_unique_constraints", [])

            # Get the columns, indexes, and unique constraints from the table schema
            for col_name, col_config in table_schema.items():
                column_args = [col_name, col_config["type"]()]
                column_kwargs = {}
                if col_config.get("primary_key", False):
                    column_kwargs["primary_key"] = True
                if "nullable" in col_config:
                    column_kwargs["nullable"] = col_config["nullable"]
                if col_config.get("index", False):
                    indexes.append(col_name)
                if col_config.get("unique", False):
                    column_kwargs["unique"] = True
                    unique_constraints.append(col_name)
                columns.append(Column(*column_args, **column_kwargs))  # type: ignore

            # Create the table object
            table_metadata = MetaData(schema=db_schema)
            table = Table(table_name, table_metadata, *columns, schema=db_schema)

            # Add multi-column unique constraints with table-specific names
            for constraint in schema_unique_constraints:
                constraint_name = f"{table_name}_{constraint['name']}"
                constraint_columns = constraint["columns"]
                table.append_constraint(UniqueConstraint(*constraint_columns, name=constraint_name))

            # Add indexes to the table definition
            for idx_col in indexes:
                idx_name = f"idx_{table_name}_{idx_col}"
                table.append_constraint(Index(idx_name, idx_col))

            async with self.async_session_factory() as sess, sess.begin():
                await create_schema(session=sess, db_schema=db_schema)

            # Create table
            async with self.db_engine.begin() as conn:
                await conn.run_sync(table.create, checkfirst=True)

            # Create indexes
            for idx in table.indexes:
                try:
                    # Check if index already exists
                    async with self.async_session_factory() as sess:
                        exists_query = text(
                            "SELECT 1 FROM pg_indexes WHERE schemaname = :schema AND indexname = :index_name"
                        )
                        result = await sess.execute(exists_query, {"schema": db_schema, "index_name": idx.name})
                        exists = result.scalar() is not None
                        if exists:
                            log_debug(f"Index {idx.name} already exists in {db_schema}.{table_name}, skipping creation")
                            continue

                    async with self.db_engine.begin() as conn:
                        await conn.run_sync(idx.create)
                    log_debug(f"Created index: {idx.name} for table {db_schema}.{table_name}")

                except Exception as e:
                    log_error(f"Error creating index {idx.name}: {e}")

            log_info(f"Successfully created table {table_name} in schema {db_schema}")
            return table

        except Exception as e:
            log_error(f"Could not create table {db_schema}.{table_name}: {e}")
            raise

    async def _get_table(self, table_type: str) -> Table:
        if table_type == "sessions":
            if not hasattr(self, "session_table"):
                self.session_table = await self._get_or_create_table(
                    table_name=self.session_table_name, table_type="sessions", db_schema=self.db_schema
                )
            return self.session_table

        if table_type == "memories":
            if not hasattr(self, "memory_table"):
                self.memory_table = await self._get_or_create_table(
                    table_name=self.memory_table_name, table_type="memories", db_schema=self.db_schema
                )
            return self.memory_table

        if table_type == "metrics":
            if not hasattr(self, "metrics_table"):
                self.metrics_table = await self._get_or_create_table(
                    table_name=self.metrics_table_name, table_type="metrics", db_schema=self.db_schema
                )
            return self.metrics_table

        if table_type == "evals":
            if not hasattr(self, "eval_table"):
                self.eval_table = await self._get_or_create_table(
                    table_name=self.eval_table_name, table_type="evals", db_schema=self.db_schema
                )
            return self.eval_table

        if table_type == "knowledge":
            if not hasattr(self, "knowledge_table"):
                self.knowledge_table = await self._get_or_create_table(
                    table_name=self.knowledge_table_name, table_type="knowledge", db_schema=self.db_schema
                )
            return self.knowledge_table

        if table_type == "culture":
            if not hasattr(self, "culture_table"):
                self.culture_table = await self._get_or_create_table(
                    table_name=self.culture_table_name, table_type="culture", db_schema=self.db_schema
                )
            return self.culture_table

        raise ValueError(f"Unknown table type: {table_type}")

    async def _get_or_create_table(self, table_name: str, table_type: str, db_schema: str) -> Table:
        """
        Check if the table exists and is valid, else create it.

        Args:
            table_name (str): Name of the table to get or create
            table_type (str): Type of table (used to get schema definition)
            db_schema (str): Database schema name

        Returns:
            Table: SQLAlchemy Table object representing the schema.
        """

        async with self.async_session_factory() as sess, sess.begin():
            table_is_available = await is_table_available(session=sess, table_name=table_name, db_schema=db_schema)

        if not table_is_available:
            return await self._create_table(table_name=table_name, table_type=table_type, db_schema=db_schema)

        if not await is_valid_table(
            db_engine=self.db_engine,
            table_name=table_name,
            table_type=table_type,
            db_schema=db_schema,
        ):
            raise ValueError(f"Table {db_schema}.{table_name} has an invalid schema")

        try:
            async with self.db_engine.connect() as conn:

                def create_table(connection):
                    return Table(table_name, self.metadata, schema=db_schema, autoload_with=connection)

                table = await conn.run_sync(create_table)
                return table

        except Exception as e:
            log_error(f"Error loading existing table {db_schema}.{table_name}: {e}")
            raise

    # -- Session methods --
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the database.

        Args:
            session_id (str): ID of the session to delete

        Returns:
            bool: True if the session was deleted, False otherwise.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="sessions")

            async with self.async_session_factory() as sess, sess.begin():
                delete_stmt = table.delete().where(table.c.session_id == session_id)
                result = await sess.execute(delete_stmt)

                if result.rowcount == 0:
                    log_debug(f"No session found to delete with session_id: {session_id} in table {table.name}")
                    return False

                else:
                    log_debug(f"Successfully deleted session with session_id: {session_id} in table {table.name}")
                    return True

        except Exception as e:
            log_error(f"Error deleting session: {e}")
            return False

    async def delete_sessions(self, session_ids: List[str]) -> None:
        """Delete all given sessions from the database.
        Can handle multiple session types in the same run.

        Args:
            session_ids (List[str]): The IDs of the sessions to delete.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="sessions")

            async with self.async_session_factory() as sess, sess.begin():
                delete_stmt = table.delete().where(table.c.session_id.in_(session_ids))
                result = await sess.execute(delete_stmt)

            log_debug(f"Successfully deleted {result.rowcount} sessions")

        except Exception as e:
            log_error(f"Error deleting sessions: {e}")

    async def get_session(
        self,
        session_id: str,
        session_type: SessionType,
        user_id: Optional[str] = None,
        deserialize: Optional[bool] = True,
    ) -> Optional[Union[Session, Dict[str, Any]]]:
        """
        Read a session from the database.

        Args:
            session_id (str): ID of the session to read.
            user_id (Optional[str]): User ID to filter by. Defaults to None.
            session_type (Optional[SessionType]): Type of session to read. Defaults to None.
            deserialize (Optional[bool]): Whether to serialize the session. Defaults to True.

        Returns:
            Union[Session, Dict[str, Any], None]:
                - When deserialize=True: Session object
                - When deserialize=False: Session dictionary

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="sessions")

            async with self.async_session_factory() as sess:
                stmt = select(table).where(table.c.session_id == session_id)

                if user_id is not None:
                    stmt = stmt.where(table.c.user_id == user_id)
                if session_type is not None:
                    session_type_value = session_type.value if isinstance(session_type, SessionType) else session_type
                    stmt = stmt.where(table.c.session_type == session_type_value)
                result = await sess.execute(stmt)
                row = result.fetchone()
                if row is None:
                    return None

                session = dict(row._mapping)

            if not deserialize:
                return session

            if session_type == SessionType.AGENT:
                return AgentSession.from_dict(session)
            elif session_type == SessionType.TEAM:
                return TeamSession.from_dict(session)
            elif session_type == SessionType.WORKFLOW:
                return WorkflowSession.from_dict(session)
            else:
                raise ValueError(f"Invalid session type: {session_type}")

        except Exception as e:
            log_error(f"Exception reading from session table: {e}")
            return None

    async def get_sessions(
        self,
        session_type: Optional[SessionType] = None,
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        session_name: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        deserialize: Optional[bool] = True,
    ) -> Union[List[Session], Tuple[List[Dict[str, Any]], int]]:
        """
        Get all sessions in the given table. Can filter by user_id and entity_id.

        Args:
            user_id (Optional[str]): The ID of the user to filter by.
            component_id (Optional[str]): The ID of the agent / workflow to filter by.
            start_timestamp (Optional[int]): The start timestamp to filter by.
            end_timestamp (Optional[int]): The end timestamp to filter by.
            session_name (Optional[str]): The name of the session to filter by.
            limit (Optional[int]): The maximum number of sessions to return. Defaults to None.
            page (Optional[int]): The page number to return. Defaults to None.
            sort_by (Optional[str]): The field to sort by. Defaults to None.
            sort_order (Optional[str]): The sort order. Defaults to None.
            deserialize (Optional[bool]): Whether to serialize the sessions. Defaults to True.

        Returns:
            Union[List[Session], Tuple[List[Dict], int]]:
                - When deserialize=True: List of Session objects
                - When deserialize=False: Tuple of (session dictionaries, total count)

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="sessions")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table)

                # Filtering
                if user_id is not None:
                    stmt = stmt.where(table.c.user_id == user_id)
                if component_id is not None:
                    if session_type == SessionType.AGENT:
                        stmt = stmt.where(table.c.agent_id == component_id)
                    elif session_type == SessionType.TEAM:
                        stmt = stmt.where(table.c.team_id == component_id)
                    elif session_type == SessionType.WORKFLOW:
                        stmt = stmt.where(table.c.workflow_id == component_id)
                if start_timestamp is not None:
                    stmt = stmt.where(table.c.created_at >= start_timestamp)
                if end_timestamp is not None:
                    stmt = stmt.where(table.c.created_at <= end_timestamp)
                if session_name is not None:
                    stmt = stmt.where(
                        func.coalesce(func.json_extract_path_text(table.c.session_data, "session_name"), "").ilike(
                            f"%{session_name}%"
                        )
                    )
                if session_type is not None:
                    session_type_value = session_type.value if isinstance(session_type, SessionType) else session_type
                    stmt = stmt.where(table.c.session_type == session_type_value)

                count_stmt = select(func.count()).select_from(stmt.alias())
                total_count = await sess.scalar(count_stmt) or 0

                # Sorting
                stmt = apply_sorting(stmt, table, sort_by, sort_order)

                # Paginating
                if limit is not None:
                    stmt = stmt.limit(limit)
                    if page is not None:
                        stmt = stmt.offset((page - 1) * limit)

                result = await sess.execute(stmt)
                records = result.fetchall()
                if records is None:
                    return [], 0

                session = [dict(record._mapping) for record in records]
                if not deserialize:
                    return session, total_count

            if session_type == SessionType.AGENT:
                return [AgentSession.from_dict(record) for record in session]  # type: ignore
            elif session_type == SessionType.TEAM:
                return [TeamSession.from_dict(record) for record in session]  # type: ignore
            elif session_type == SessionType.WORKFLOW:
                return [WorkflowSession.from_dict(record) for record in session]  # type: ignore
            else:
                raise ValueError(f"Invalid session type: {session_type}")

        except Exception as e:
            log_error(f"Exception reading from session table: {e}")
            return [] if deserialize else ([], 0)

    async def rename_session(
        self, session_id: str, session_type: SessionType, session_name: str, deserialize: Optional[bool] = True
    ) -> Optional[Union[Session, Dict[str, Any]]]:
        """
        Rename a session in the database.

        Args:
            session_id (str): The ID of the session to rename.
            session_type (SessionType): The type of session to rename.
            session_name (str): The new name for the session.
            deserialize (Optional[bool]): Whether to serialize the session. Defaults to True.

        Returns:
            Optional[Union[Session, Dict[str, Any]]]:
                - When deserialize=True: Session object
                - When deserialize=False: Session dictionary

        Raises:
            Exception: If an error occurs during renaming.
        """
        try:
            table = await self._get_table(table_type="sessions")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = (
                    update(table)
                    .where(table.c.session_id == session_id)
                    .where(table.c.session_type == session_type.value)
                    .values(
                        session_data=func.cast(
                            func.jsonb_set(
                                func.cast(table.c.session_data, postgresql.JSONB),
                                text("'{session_name}'"),
                                func.to_jsonb(session_name),
                            ),
                            postgresql.JSON,
                        )
                    )
                    .returning(*table.c)
                )
                result = await sess.execute(stmt)
                row = result.fetchone()
                if not row:
                    return None

            log_debug(f"Renamed session with id '{session_id}' to '{session_name}'")

            session = dict(row._mapping)
            if not deserialize:
                return session

            # Return the appropriate session type
            if session_type == SessionType.AGENT:
                return AgentSession.from_dict(session)
            elif session_type == SessionType.TEAM:
                return TeamSession.from_dict(session)
            elif session_type == SessionType.WORKFLOW:
                return WorkflowSession.from_dict(session)
            else:
                raise ValueError(f"Invalid session type: {session_type}")

        except Exception as e:
            log_error(f"Exception renaming session: {e}")
            return None

    async def upsert_session(
        self, session: Session, deserialize: Optional[bool] = True
    ) -> Optional[Union[Session, Dict[str, Any]]]:
        """
        Insert or update a session in the database.

        Args:
            session (Session): The session data to upsert.
            deserialize (Optional[bool]): Whether to deserialize the session. Defaults to True.

        Returns:
            Optional[Union[Session, Dict[str, Any]]]:
                - When deserialize=True: Session object
                - When deserialize=False: Session dictionary

        Raises:
            Exception: If an error occurs during upsert.
        """
        try:
            table = await self._get_table(table_type="sessions")
            session_dict = session.to_dict()

            if isinstance(session, AgentSession):
                async with self.async_session_factory() as sess, sess.begin():
                    stmt = postgresql.insert(table).values(
                        session_id=session_dict.get("session_id"),
                        session_type=SessionType.AGENT.value,
                        agent_id=session_dict.get("agent_id"),
                        user_id=session_dict.get("user_id"),
                        runs=session_dict.get("runs"),
                        agent_data=session_dict.get("agent_data"),
                        session_data=session_dict.get("session_data"),
                        summary=session_dict.get("summary"),
                        metadata=session_dict.get("metadata"),
                        created_at=session_dict.get("created_at"),
                        updated_at=session_dict.get("created_at"),
                    )
                    stmt = stmt.on_conflict_do_update(  # type: ignore
                        index_elements=["session_id"],
                        set_=dict(
                            agent_id=session_dict.get("agent_id"),
                            user_id=session_dict.get("user_id"),
                            agent_data=session_dict.get("agent_data"),
                            session_data=session_dict.get("session_data"),
                            summary=session_dict.get("summary"),
                            metadata=session_dict.get("metadata"),
                            runs=session_dict.get("runs"),
                            updated_at=int(time.time()),
                        ),
                    ).returning(table)
                    result = await sess.execute(stmt)
                    row = result.fetchone()
                    if row is None:
                        return None
                    session_dict = dict(row._mapping)

                    log_debug(f"Upserted agent session with id '{session_dict.get('session_id')}'")

                    if not deserialize:
                        return session_dict
                    return AgentSession.from_dict(session_dict)

            elif isinstance(session, TeamSession):
                async with self.async_session_factory() as sess, sess.begin():
                    stmt = postgresql.insert(table).values(
                        session_id=session_dict.get("session_id"),
                        session_type=SessionType.TEAM.value,
                        team_id=session_dict.get("team_id"),
                        user_id=session_dict.get("user_id"),
                        runs=session_dict.get("runs"),
                        team_data=session_dict.get("team_data"),
                        session_data=session_dict.get("session_data"),
                        summary=session_dict.get("summary"),
                        metadata=session_dict.get("metadata"),
                        created_at=session_dict.get("created_at"),
                        updated_at=session_dict.get("created_at"),
                    )
                    stmt = stmt.on_conflict_do_update(  # type: ignore
                        index_elements=["session_id"],
                        set_=dict(
                            team_id=session_dict.get("team_id"),
                            user_id=session_dict.get("user_id"),
                            team_data=session_dict.get("team_data"),
                            session_data=session_dict.get("session_data"),
                            summary=session_dict.get("summary"),
                            metadata=session_dict.get("metadata"),
                            runs=session_dict.get("runs"),
                            updated_at=int(time.time()),
                        ),
                    ).returning(table)
                    result = await sess.execute(stmt)
                    row = result.fetchone()
                    if row is None:
                        return None
                    session_dict = dict(row._mapping)

                    log_debug(f"Upserted team session with id '{session_dict.get('session_id')}'")

                    if not deserialize:
                        return session_dict
                    return TeamSession.from_dict(session_dict)

            elif isinstance(session, WorkflowSession):
                async with self.async_session_factory() as sess, sess.begin():
                    stmt = postgresql.insert(table).values(
                        session_id=session_dict.get("session_id"),
                        session_type=SessionType.WORKFLOW.value,
                        workflow_id=session_dict.get("workflow_id"),
                        user_id=session_dict.get("user_id"),
                        runs=session_dict.get("runs"),
                        workflow_data=session_dict.get("workflow_data"),
                        session_data=session_dict.get("session_data"),
                        summary=session_dict.get("summary"),
                        metadata=session_dict.get("metadata"),
                        created_at=session_dict.get("created_at"),
                        updated_at=session_dict.get("created_at"),
                    )
                    stmt = stmt.on_conflict_do_update(  # type: ignore
                        index_elements=["session_id"],
                        set_=dict(
                            workflow_id=session_dict.get("workflow_id"),
                            user_id=session_dict.get("user_id"),
                            workflow_data=session_dict.get("workflow_data"),
                            session_data=session_dict.get("session_data"),
                            summary=session_dict.get("summary"),
                            metadata=session_dict.get("metadata"),
                            runs=session_dict.get("runs"),
                            updated_at=int(time.time()),
                        ),
                    ).returning(table)
                    result = await sess.execute(stmt)
                    row = result.fetchone()
                    if row is None:
                        return None
                    session_dict = dict(row._mapping)

                    log_debug(f"Upserted workflow session with id '{session_dict.get('session_id')}'")

                    if not deserialize:
                        return session_dict
                    return WorkflowSession.from_dict(session_dict)

            else:
                raise ValueError(f"Invalid session type: {session.session_type}")

        except Exception as e:
            log_error(f"Exception upserting into sessions table: {e}")
            return None

    # -- Memory methods --
    async def delete_user_memory(self, memory_id: str):
        """Delete a user memory from the database.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                delete_stmt = table.delete().where(table.c.memory_id == memory_id)
                result = await sess.execute(delete_stmt)

                success = result.rowcount > 0
                if success:
                    log_debug(f"Successfully deleted user memory id: {memory_id}")
                else:
                    log_debug(f"No user memory found with id: {memory_id}")

        except Exception as e:
            log_error(f"Error deleting user memory: {e}")

    async def delete_user_memories(self, memory_ids: List[str]) -> None:
        """Delete user memories from the database.

        Args:
            memory_ids (List[str]): The IDs of the memories to delete.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                delete_stmt = table.delete().where(table.c.memory_id.in_(memory_ids))
                result = await sess.execute(delete_stmt)

                if result.rowcount == 0:
                    log_debug(f"No user memories found with ids: {memory_ids}")
                else:
                    log_debug(f"Successfully deleted {result.rowcount} user memories")

        except Exception as e:
            log_error(f"Error deleting user memories: {e}")

    async def get_all_memory_topics(self) -> List[str]:
        """Get all memory topics from the database.

        Returns:
            List[str]: List of memory topics.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(func.json_array_elements_text(table.c.topics))
                result = await sess.execute(stmt)
                records = result.fetchall()

                return list(set([record[0] for record in records]))

        except Exception as e:
            log_error(f"Exception reading from memory table: {e}")
            return []

    async def get_user_memory(
        self, memory_id: str, deserialize: Optional[bool] = True
    ) -> Optional[Union[UserMemory, Dict[str, Any]]]:
        """Get a memory from the database.

        Args:
            memory_id (str): The ID of the memory to get.
            deserialize (Optional[bool]): Whether to serialize the memory. Defaults to True.

        Returns:
            Union[UserMemory, Dict[str, Any], None]:
                - When deserialize=True: UserMemory object
                - When deserialize=False: UserMemory dictionary

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table).where(table.c.memory_id == memory_id)

                result = await sess.execute(stmt)
                row = result.fetchone()
                if not row:
                    return None

                memory_raw = dict(row._mapping)
                if not deserialize:
                    return memory_raw

            return UserMemory.from_dict(memory_raw)

        except Exception as e:
            log_error(f"Exception reading from memory table: {e}")
            return None

    async def get_user_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        topics: Optional[List[str]] = None,
        search_content: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        deserialize: Optional[bool] = True,
    ) -> Union[List[UserMemory], Tuple[List[Dict[str, Any]], int]]:
        """Get all memories from the database as UserMemory objects.

        Args:
            user_id (Optional[str]): The ID of the user to filter by.
            agent_id (Optional[str]): The ID of the agent to filter by.
            team_id (Optional[str]): The ID of the team to filter by.
            topics (Optional[List[str]]): The topics to filter by.
            search_content (Optional[str]): The content to search for.
            limit (Optional[int]): The maximum number of memories to return.
            page (Optional[int]): The page number.
            sort_by (Optional[str]): The column to sort by.
            sort_order (Optional[str]): The order to sort by.
            deserialize (Optional[bool]): Whether to serialize the memories. Defaults to True.

        Returns:
            Union[List[UserMemory], Tuple[List[Dict[str, Any]], int]]:
                - When deserialize=True: List of UserMemory objects
                - When deserialize=False: Tuple of (memory dictionaries, total count)

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table)
                # Filtering
                if user_id is not None:
                    stmt = stmt.where(table.c.user_id == user_id)
                if agent_id is not None:
                    stmt = stmt.where(table.c.agent_id == agent_id)
                if team_id is not None:
                    stmt = stmt.where(table.c.team_id == team_id)
                if topics is not None:
                    for topic in topics:
                        stmt = stmt.where(func.cast(table.c.topics, String).like(f'%"{topic}"%'))
                if search_content is not None:
                    stmt = stmt.where(func.cast(table.c.memory, postgresql.TEXT).ilike(f"%{search_content}%"))

                # Get total count after applying filtering
                count_stmt = select(func.count()).select_from(stmt.alias())
                total_count = await sess.scalar(count_stmt) or 0

                # Sorting
                stmt = apply_sorting(stmt, table, sort_by, sort_order)

                # Paginating
                if limit is not None:
                    stmt = stmt.limit(limit)
                    if page is not None:
                        stmt = stmt.offset((page - 1) * limit)

                result = await sess.execute(stmt)
                records = result.fetchall()
                if not records:
                    return [] if deserialize else ([], 0)

                memories_raw = [dict(record._mapping) for record in records]
                if not deserialize:
                    return memories_raw, total_count

            return [UserMemory.from_dict(record) for record in memories_raw]

        except Exception as e:
            log_error(f"Exception reading from memory table: {e}")
            return [] if deserialize else ([], 0)

    async def clear_memories(self) -> None:
        """Delete all memories from the database.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                await sess.execute(table.delete())

        except Exception as e:
            log_warning(f"Exception deleting all memories: {e}")

    # -- Cultural Knowledge methods --
    async def clear_cultural_knowledge(self) -> None:
        """Delete all cultural knowledge from the database.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="culture")

            async with self.async_session_factory() as sess, sess.begin():
                await sess.execute(table.delete())

        except Exception as e:
            log_warning(f"Exception deleting all cultural knowledge: {e}")

    async def delete_cultural_knowledge(self, id: str) -> None:
        """Delete cultural knowledge by ID.

        Args:
            id (str): The ID of the cultural knowledge to delete.

        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            table = await self._get_table(table_type="culture")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = table.delete().where(table.c.id == id)
                await sess.execute(stmt)

        except Exception as e:
            log_warning(f"Exception deleting cultural knowledge: {e}")
            raise e

    async def get_cultural_knowledge(
        self, id: str, deserialize: Optional[bool] = True
    ) -> Optional[Union[CulturalKnowledge, Dict[str, Any]]]:
        """Get cultural knowledge by ID.

        Args:
            id (str): The ID of the cultural knowledge to retrieve.
            deserialize (Optional[bool]): Whether to deserialize to CulturalKnowledge object. Defaults to True.

        Returns:
            Optional[Union[CulturalKnowledge, Dict[str, Any]]]: The cultural knowledge if found, None otherwise.

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="culture")

            async with self.async_session_factory() as sess:
                stmt = select(table).where(table.c.id == id)
                result = await sess.execute(stmt)
                row = result.fetchone()

                if row is None:
                    return None

                db_row = dict(row._mapping)

                if not deserialize:
                    return db_row

                return deserialize_cultural_knowledge(db_row)

        except Exception as e:
            log_warning(f"Exception reading cultural knowledge: {e}")
            raise e

    async def get_all_cultural_knowledge(
        self,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        name: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        deserialize: Optional[bool] = True,
    ) -> Union[List[CulturalKnowledge], Tuple[List[Dict[str, Any]], int]]:
        """Get all cultural knowledge with filtering and pagination.

        Args:
            agent_id (Optional[str]): Filter by agent ID.
            team_id (Optional[str]): Filter by team ID.
            name (Optional[str]): Filter by name (case-insensitive partial match).
            limit (Optional[int]): Maximum number of results to return.
            page (Optional[int]): Page number for pagination.
            sort_by (Optional[str]): Field to sort by.
            sort_order (Optional[str]): Sort order ('asc' or 'desc').
            deserialize (Optional[bool]): Whether to deserialize to CulturalKnowledge objects. Defaults to True.

        Returns:
            Union[List[CulturalKnowledge], Tuple[List[Dict[str, Any]], int]]:
                - When deserialize=True: List of CulturalKnowledge objects
                - When deserialize=False: Tuple with list of dictionaries and total count

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="culture")

            async with self.async_session_factory() as sess:
                # Build query with filters
                stmt = select(table)
                if agent_id is not None:
                    stmt = stmt.where(table.c.agent_id == agent_id)
                if team_id is not None:
                    stmt = stmt.where(table.c.team_id == team_id)
                if name is not None:
                    stmt = stmt.where(table.c.name.ilike(f"%{name}%"))

                # Get total count
                count_stmt = select(func.count()).select_from(stmt.alias())
                total_count_result = await sess.execute(count_stmt)
                total_count = total_count_result.scalar() or 0

                # Apply sorting
                stmt = apply_sorting(stmt, table, sort_by, sort_order)

                # Apply pagination
                if limit is not None:
                    stmt = stmt.limit(limit)
                    if page is not None:
                        stmt = stmt.offset((page - 1) * limit)

                # Execute query
                result = await sess.execute(stmt)
                rows = result.fetchall()

                db_rows = [dict(row._mapping) for row in rows]

                if not deserialize:
                    return db_rows, total_count

                return [deserialize_cultural_knowledge(row) for row in db_rows]

        except Exception as e:
            log_warning(f"Exception reading all cultural knowledge: {e}")
            raise e

    async def upsert_cultural_knowledge(
        self, cultural_knowledge: CulturalKnowledge, deserialize: Optional[bool] = True
    ) -> Optional[Union[CulturalKnowledge, Dict[str, Any]]]:
        """Upsert cultural knowledge in the database.

        Args:
            cultural_knowledge (CulturalKnowledge): The cultural knowledge to upsert.
            deserialize (Optional[bool]): Whether to deserialize the result. Defaults to True.

        Returns:
            Optional[Union[CulturalKnowledge, Dict[str, Any]]]: The upserted cultural knowledge.

        Raises:
            Exception: If an error occurs during upsert.
        """
        try:
            table = await self._get_table(table_type="culture")

            # Generate ID if not present
            if cultural_knowledge.id is None:
                cultural_knowledge.id = str(uuid4())

            # Serialize content, categories, and notes into a JSON dict for DB storage
            content_dict = serialize_cultural_knowledge(cultural_knowledge)

            async with self.async_session_factory() as sess, sess.begin():
                # Use PostgreSQL-specific insert with on_conflict_do_update
                insert_stmt = postgresql.insert(table).values(
                    id=cultural_knowledge.id,
                    name=cultural_knowledge.name,
                    summary=cultural_knowledge.summary,
                    content=content_dict if content_dict else None,
                    metadata=cultural_knowledge.metadata,
                    input=cultural_knowledge.input,
                    created_at=cultural_knowledge.created_at,
                    updated_at=int(time.time()),
                    agent_id=cultural_knowledge.agent_id,
                    team_id=cultural_knowledge.team_id,
                )

                # Update all fields except id on conflict
                update_dict = {
                    "name": cultural_knowledge.name,
                    "summary": cultural_knowledge.summary,
                    "content": content_dict if content_dict else None,
                    "metadata": cultural_knowledge.metadata,
                    "input": cultural_knowledge.input,
                    "updated_at": int(time.time()),
                    "agent_id": cultural_knowledge.agent_id,
                    "team_id": cultural_knowledge.team_id,
                }
                upsert_stmt = insert_stmt.on_conflict_do_update(index_elements=["id"], set_=update_dict).returning(
                    table
                )

                result = await sess.execute(upsert_stmt)
                row = result.fetchone()

                if row is None:
                    return None

                db_row = dict(row._mapping)

            if not deserialize:
                return db_row

            # Deserialize from DB format to model format
            return deserialize_cultural_knowledge(db_row)

        except Exception as e:
            log_warning(f"Exception upserting cultural knowledge: {e}")
            raise e

    async def get_user_memory_stats(
        self, limit: Optional[int] = None, page: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get user memories stats.

        Args:
            limit (Optional[int]): The maximum number of user stats to return.
            page (Optional[int]): The page number.

        Returns:
            Tuple[List[Dict[str, Any]], int]: A list of dictionaries containing user stats and total count.

        Example:
        (
            [
                {
                    "user_id": "123",
                    "total_memories": 10,
                    "last_memory_updated_at": 1714560000,
                },
            ],
            total_count: 1,
        )
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = (
                    select(
                        table.c.user_id,
                        func.count(table.c.memory_id).label("total_memories"),
                        func.max(table.c.updated_at).label("last_memory_updated_at"),
                    )
                    .where(table.c.user_id.is_not(None))
                    .group_by(table.c.user_id)
                    .order_by(func.max(table.c.updated_at).desc())
                )

                count_stmt = select(func.count()).select_from(stmt.alias())
                total_count = await sess.scalar(count_stmt) or 0

                # Pagination
                if limit is not None:
                    stmt = stmt.limit(limit)
                    if page is not None:
                        stmt = stmt.offset((page - 1) * limit)

                result = await sess.execute(stmt)
                records = result.fetchall()
                if not records:
                    return [], 0

                return [
                    {
                        "user_id": record.user_id,  # type: ignore
                        "total_memories": record.total_memories,
                        "last_memory_updated_at": record.last_memory_updated_at,
                    }
                    for record in records
                ], total_count

        except Exception as e:
            log_error(f"Exception getting user memory stats: {e}")
            return [], 0

    async def upsert_user_memory(
        self, memory: UserMemory, deserialize: Optional[bool] = True
    ) -> Optional[Union[UserMemory, Dict[str, Any]]]:
        """Upsert a user memory in the database.

        Args:
            memory (UserMemory): The user memory to upsert.
            deserialize (Optional[bool]): Whether to serialize the memory. Defaults to True.

        Returns:
            Optional[Union[UserMemory, Dict[str, Any]]]:
                - When deserialize=True: UserMemory object
                - When deserialize=False: UserMemory dictionary

        Raises:
            Exception: If an error occurs during upsert.
        """
        try:
            table = await self._get_table(table_type="memories")

            async with self.async_session_factory() as sess, sess.begin():
                if memory.memory_id is None:
                    memory.memory_id = str(uuid4())

                stmt = postgresql.insert(table).values(
                    memory_id=memory.memory_id,
                    memory=memory.memory,
                    input=memory.input,
                    user_id=memory.user_id,
                    agent_id=memory.agent_id,
                    team_id=memory.team_id,
                    topics=memory.topics,
                    updated_at=int(time.time()),
                )
                stmt = stmt.on_conflict_do_update(  # type: ignore
                    index_elements=["memory_id"],
                    set_=dict(
                        memory=memory.memory,
                        topics=memory.topics,
                        input=memory.input,
                        agent_id=memory.agent_id,
                        team_id=memory.team_id,
                        updated_at=int(time.time()),
                    ),
                ).returning(table)

                result = await sess.execute(stmt)
                row = result.fetchone()
                if row is None:
                    return None

            memory_raw = dict(row._mapping)

            log_debug(f"Upserted user memory with id '{memory.memory_id}'")

            if not memory_raw or not deserialize:
                return memory_raw

            return UserMemory.from_dict(memory_raw)

        except Exception as e:
            log_error(f"Exception upserting user memory: {e}")
            return None

    # -- Metrics methods --
    async def _get_all_sessions_for_metrics_calculation(
        self, start_timestamp: Optional[int] = None, end_timestamp: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions of all types (agent, team, workflow) as raw dictionaries.

         Args:
            start_timestamp (Optional[int]): The start timestamp to filter by. Defaults to None.
            end_timestamp (Optional[int]): The end timestamp to filter by. Defaults to None.

        Returns:
            List[Dict[str, Any]]: List of session dictionaries with session_type field.

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="sessions")

            stmt = select(
                table.c.user_id,
                table.c.session_data,
                table.c.runs,
                table.c.created_at,
                table.c.session_type,
            )

            if start_timestamp is not None:
                stmt = stmt.where(table.c.created_at >= start_timestamp)
            if end_timestamp is not None:
                stmt = stmt.where(table.c.created_at <= end_timestamp)

            async with self.async_session_factory() as sess:
                result = await sess.execute(stmt)
                records = result.fetchall()

                return [dict(record._mapping) for record in records]

        except Exception as e:
            log_error(f"Exception reading from sessions table: {e}")
            return []

    async def _get_metrics_calculation_starting_date(self, table: Table) -> Optional[date]:
        """Get the first date for which metrics calculation is needed:

        1. If there are metrics records, return the date of the first day without a complete metrics record.
        2. If there are no metrics records, return the date of the first recorded session.
        3. If there are no metrics records and no sessions records, return None.

        Args:
            table (Table): The table to get the starting date for.

        Returns:
            Optional[date]: The starting date for which metrics calculation is needed.
        """
        async with self.async_session_factory() as sess:
            stmt = select(table).order_by(table.c.date.desc()).limit(1)
            result = await sess.execute(stmt)
            row = result.fetchone()

            # 1. Return the date of the first day without a complete metrics record.
            if row is not None:
                if row.completed:
                    return row._mapping["date"] + timedelta(days=1)
                else:
                    return row._mapping["date"]

        # 2. No metrics records. Return the date of the first recorded session.
        first_session, _ = await self.get_sessions(sort_by="created_at", sort_order="asc", limit=1, deserialize=False)

        first_session_date = first_session[0]["created_at"] if first_session else None  # type: ignore[index]

        # 3. No metrics records and no sessions records. Return None.
        if first_session_date is None:
            return None

        return datetime.fromtimestamp(first_session_date, tz=timezone.utc).date()

    async def calculate_metrics(self) -> Optional[list[dict]]:
        """Calculate metrics for all dates without complete metrics.

        Returns:
            Optional[list[dict]]: The calculated metrics.

        Raises:
            Exception: If an error occurs during metrics calculation.
        """
        try:
            table = await self._get_table(table_type="metrics")

            starting_date = await self._get_metrics_calculation_starting_date(table)

            if starting_date is None:
                log_info("No session data found. Won't calculate metrics.")
                return None

            dates_to_process = get_dates_to_calculate_metrics_for(starting_date)
            if not dates_to_process:
                log_info("Metrics already calculated for all relevant dates.")
                return None

            start_timestamp = int(
                datetime.combine(dates_to_process[0], datetime.min.time()).replace(tzinfo=timezone.utc).timestamp()
            )
            end_timestamp = int(
                datetime.combine(dates_to_process[-1] + timedelta(days=1), datetime.min.time())
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )

            sessions = await self._get_all_sessions_for_metrics_calculation(
                start_timestamp=start_timestamp, end_timestamp=end_timestamp
            )

            all_sessions_data = fetch_all_sessions_data(
                sessions=sessions, dates_to_process=dates_to_process, start_timestamp=start_timestamp
            )
            if not all_sessions_data:
                log_info("No new session data found. Won't calculate metrics.")
                return None

            results = []
            metrics_records = []

            for date_to_process in dates_to_process:
                date_key = date_to_process.isoformat()
                sessions_for_date = all_sessions_data.get(date_key, {})

                # Skip dates with no sessions
                if not any(len(sessions) > 0 for sessions in sessions_for_date.values()):
                    continue

                metrics_record = calculate_date_metrics(date_to_process, sessions_for_date)

                metrics_records.append(metrics_record)

            if metrics_records:
                async with self.async_session_factory() as sess, sess.begin():
                    results = await bulk_upsert_metrics(session=sess, table=table, metrics_records=metrics_records)

            log_debug("Updated metrics calculations")

            return results

        except Exception as e:
            log_error(f"Exception refreshing metrics: {e}")
            return None

    async def get_metrics(
        self, starting_date: Optional[date] = None, ending_date: Optional[date] = None
    ) -> Tuple[List[dict], Optional[int]]:
        """Get all metrics matching the given date range.

        Args:
            starting_date (Optional[date]): The starting date to filter metrics by.
            ending_date (Optional[date]): The ending date to filter metrics by.

        Returns:
            Tuple[List[dict], Optional[int]]: A tuple containing the metrics and the timestamp of the latest update.

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="metrics")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table)
                if starting_date:
                    stmt = stmt.where(table.c.date >= starting_date)
                if ending_date:
                    stmt = stmt.where(table.c.date <= ending_date)
                result = await sess.execute(stmt)
                records = result.fetchall()
                if not records:
                    return [], None

                # Get the latest updated_at
                latest_stmt = select(func.max(table.c.updated_at))
                latest_result = await sess.execute(latest_stmt)
                latest_updated_at = latest_result.scalar()

            return [dict(row._mapping) for row in records], latest_updated_at

        except Exception as e:
            log_warning(f"Exception getting metrics: {e}")
            return [], None

    # -- Knowledge methods --
    async def delete_knowledge_content(self, id: str):
        """Delete a knowledge row from the database.

        Args:
            id (str): The ID of the knowledge row to delete.
        """
        table = await self._get_table(table_type="knowledge")

        try:
            async with self.async_session_factory() as sess, sess.begin():
                stmt = table.delete().where(table.c.id == id)
                await sess.execute(stmt)

        except Exception as e:
            log_error(f"Exception deleting knowledge content: {e}")

    async def get_knowledge_content(self, id: str) -> Optional[KnowledgeRow]:
        """Get a knowledge row from the database.

        Args:
            id (str): The ID of the knowledge row to get.

        Returns:
            Optional[KnowledgeRow]: The knowledge row, or None if it doesn't exist.
        """
        table = await self._get_table(table_type="knowledge")

        try:
            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table).where(table.c.id == id)
                result = await sess.execute(stmt)
                row = result.fetchone()
                if row is None:
                    return None

                return KnowledgeRow.model_validate(row._mapping)

        except Exception as e:
            log_error(f"Exception getting knowledge content: {e}")
            return None

    async def get_knowledge_contents(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Tuple[List[KnowledgeRow], int]:
        """Get all knowledge contents from the database.

        Args:
            limit (Optional[int]): The maximum number of knowledge contents to return.
            page (Optional[int]): The page number.
            sort_by (Optional[str]): The column to sort by.
            sort_order (Optional[str]): The order to sort by.

        Returns:
            List[KnowledgeRow]: The knowledge contents.

        Raises:
            Exception: If an error occurs during retrieval.
        """
        table = await self._get_table(table_type="knowledge")

        try:
            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table)

                # Apply sorting
                if sort_by is not None:
                    stmt = stmt.order_by(getattr(table.c, sort_by) * (1 if sort_order == "asc" else -1))

                # Get total count before applying limit and pagination
                count_stmt = select(func.count()).select_from(stmt.alias())
                total_count = await sess.scalar(count_stmt) or 0

                # Apply pagination after count
                if limit is not None:
                    stmt = stmt.limit(limit)
                    if page is not None:
                        stmt = stmt.offset((page - 1) * limit)

                result = await sess.execute(stmt)
                records = result.fetchall()
                return [KnowledgeRow.model_validate(record._mapping) for record in records], total_count

        except Exception as e:
            log_error(f"Exception getting knowledge contents: {e}")
            return [], 0

    async def upsert_knowledge_content(self, knowledge_row: KnowledgeRow):
        """Upsert knowledge content in the database.

        Args:
            knowledge_row (KnowledgeRow): The knowledge row to upsert.

        Returns:
            Optional[KnowledgeRow]: The upserted knowledge row, or None if the operation fails.
        """
        try:
            table = await self._get_table(table_type="knowledge")
            async with self.async_session_factory() as sess, sess.begin():
                # Get the actual table columns to avoid "unconsumed column names" error
                table_columns = set(table.columns.keys())

                # Only include fields that exist in the table and are not None
                insert_data = {}
                update_fields = {}

                # Map of KnowledgeRow fields to table columns
                field_mapping = {
                    "id": "id",
                    "name": "name",
                    "description": "description",
                    "metadata": "metadata",
                    "type": "type",
                    "size": "size",
                    "linked_to": "linked_to",
                    "access_count": "access_count",
                    "status": "status",
                    "status_message": "status_message",
                    "created_at": "created_at",
                    "updated_at": "updated_at",
                    "external_id": "external_id",
                }

                # Build insert and update data only for fields that exist in the table
                for model_field, table_column in field_mapping.items():
                    if table_column in table_columns:
                        value = getattr(knowledge_row, model_field, None)
                        if value is not None:
                            insert_data[table_column] = value
                            # Don't include ID in update_fields since it's the primary key
                            if table_column != "id":
                                update_fields[table_column] = value

                # Ensure id is always included for the insert
                if "id" in table_columns and knowledge_row.id:
                    insert_data["id"] = knowledge_row.id

                # Handle case where update_fields is empty (all fields are None or don't exist in table)
                if not update_fields:
                    # If we have insert_data, just do an insert without conflict resolution
                    if insert_data:
                        stmt = postgresql.insert(table).values(insert_data)
                        await sess.execute(stmt)
                    else:
                        # If we have no data at all, this is an error
                        log_error("No valid fields found for knowledge row upsert")
                        return None
                else:
                    # Normal upsert with conflict resolution
                    stmt = (
                        postgresql.insert(table)
                        .values(insert_data)
                        .on_conflict_do_update(index_elements=["id"], set_=update_fields)
                    )
                    await sess.execute(stmt)

            log_debug(f"Upserted knowledge row with id '{knowledge_row.id}'")

            return knowledge_row

        except Exception as e:
            log_error(f"Error upserting knowledge row: {e}")
            return None

    # -- Eval methods --
    async def create_eval_run(self, eval_run: EvalRunRecord) -> Optional[EvalRunRecord]:
        """Create an EvalRunRecord in the database.

        Args:
            eval_run (EvalRunRecord): The eval run to create.

        Returns:
            Optional[EvalRunRecord]: The created eval run, or None if the operation fails.

        Raises:
            Exception: If an error occurs during creation.
        """
        try:
            table = await self._get_table(table_type="evals")

            async with self.async_session_factory() as sess, sess.begin():
                current_time = int(time.time())
                stmt = postgresql.insert(table).values(
                    {"created_at": current_time, "updated_at": current_time, **eval_run.model_dump()}
                )
                await sess.execute(stmt)

            log_debug(f"Created eval run with id '{eval_run.run_id}'")

            return eval_run

        except Exception as e:
            log_error(f"Error creating eval run: {e}")
            return None

    async def delete_eval_run(self, eval_run_id: str) -> None:
        """Delete an eval run from the database.

        Args:
            eval_run_id (str): The ID of the eval run to delete.
        """
        try:
            table = await self._get_table(table_type="evals")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = table.delete().where(table.c.run_id == eval_run_id)
                result = await sess.execute(stmt)

                if result.rowcount == 0:
                    log_warning(f"No eval run found with ID: {eval_run_id}")
                else:
                    log_debug(f"Deleted eval run with ID: {eval_run_id}")

        except Exception as e:
            log_error(f"Error deleting eval run {eval_run_id}: {e}")

    async def delete_eval_runs(self, eval_run_ids: List[str]) -> None:
        """Delete multiple eval runs from the database.

        Args:
            eval_run_ids (List[str]): List of eval run IDs to delete.
        """
        try:
            table = await self._get_table(table_type="evals")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = table.delete().where(table.c.run_id.in_(eval_run_ids))
                result = await sess.execute(stmt)

                if result.rowcount == 0:
                    log_warning(f"No eval runs found with IDs: {eval_run_ids}")
                else:
                    log_debug(f"Deleted {result.rowcount} eval runs")

        except Exception as e:
            log_error(f"Error deleting eval runs {eval_run_ids}: {e}")

    async def get_eval_run(
        self, eval_run_id: str, deserialize: Optional[bool] = True
    ) -> Optional[Union[EvalRunRecord, Dict[str, Any]]]:
        """Get an eval run from the database.

        Args:
            eval_run_id (str): The ID of the eval run to get.
            deserialize (Optional[bool]): Whether to serialize the eval run. Defaults to True.

        Returns:
            Optional[Union[EvalRunRecord, Dict[str, Any]]]:
                - When deserialize=True: EvalRunRecord object
                - When deserialize=False: EvalRun dictionary

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="evals")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table).where(table.c.run_id == eval_run_id)
                result = await sess.execute(stmt)
                row = result.fetchone()
                if row is None:
                    return None

                eval_run_raw = dict(row._mapping)
                if not deserialize:
                    return eval_run_raw

                return EvalRunRecord.model_validate(eval_run_raw)

        except Exception as e:
            log_error(f"Exception getting eval run {eval_run_id}: {e}")
            return None

    async def get_eval_runs(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        model_id: Optional[str] = None,
        filter_type: Optional[EvalFilterType] = None,
        eval_type: Optional[List[EvalType]] = None,
        deserialize: Optional[bool] = True,
    ) -> Union[List[EvalRunRecord], Tuple[List[Dict[str, Any]], int]]:
        """Get all eval runs from the database.

        Args:
            limit (Optional[int]): The maximum number of eval runs to return.
            page (Optional[int]): The page number.
            sort_by (Optional[str]): The column to sort by.
            sort_order (Optional[str]): The order to sort by.
            agent_id (Optional[str]): The ID of the agent to filter by.
            team_id (Optional[str]): The ID of the team to filter by.
            workflow_id (Optional[str]): The ID of the workflow to filter by.
            model_id (Optional[str]): The ID of the model to filter by.
            eval_type (Optional[List[EvalType]]): The type(s) of eval to filter by.
            filter_type (Optional[EvalFilterType]): Filter by component type (agent, team, workflow).
            deserialize (Optional[bool]): Whether to serialize the eval runs. Defaults to True.

        Returns:
            Union[List[EvalRunRecord], Tuple[List[Dict[str, Any]], int]]:
                - When deserialize=True: List of EvalRunRecord objects
                - When deserialize=False: List of dictionaries

        Raises:
            Exception: If an error occurs during retrieval.
        """
        try:
            table = await self._get_table(table_type="evals")

            async with self.async_session_factory() as sess, sess.begin():
                stmt = select(table)

                # Filtering
                if agent_id is not None:
                    stmt = stmt.where(table.c.agent_id == agent_id)
                if team_id is not None:
                    stmt = stmt.where(table.c.team_id == team_id)
                if workflow_id is not None:
                    stmt = stmt.where(table.c.workflow_id == workflow_id)
                if model_id is not None:
                    stmt = stmt.where(table.c.model_id == model_id)
                if eval_type is not None and len(eval_type) > 0:
                    stmt = stmt.where(table.c.eval_type.in_(eval_type))
                if filter_type is not None:
                    if filter_type == EvalFilterType.AGENT:
                        stmt = stmt.where(table.c.agent_id.is_not(None))
                    elif filter_type == EvalFilterType.TEAM:
                        stmt = stmt.where(table.c.team_id.is_not(None))
                    elif filter_type == EvalFilterType.WORKFLOW:
                        stmt = stmt.where(table.c.workflow_id.is_not(None))

                # Get total count after applying filtering
                count_stmt = select(func.count()).select_from(stmt.alias())
                total_count = await sess.scalar(count_stmt) or 0

                # Sorting
                if sort_by is None:
                    stmt = stmt.order_by(table.c.created_at.desc())
                else:
                    stmt = apply_sorting(stmt, table, sort_by, sort_order)

                # Paginating
                if limit is not None:
                    stmt = stmt.limit(limit)
                    if page is not None:
                        stmt = stmt.offset((page - 1) * limit)

                result = await sess.execute(stmt)
                records = result.fetchall()
                if not records:
                    return [] if deserialize else ([], 0)

                eval_runs_raw = [dict(row._mapping) for row in records]
                if not deserialize:
                    return eval_runs_raw, total_count

                return [EvalRunRecord.model_validate(row) for row in eval_runs_raw]

        except Exception as e:
            log_error(f"Exception getting eval runs: {e}")
            return [] if deserialize else ([], 0)

    async def rename_eval_run(
        self, eval_run_id: str, name: str, deserialize: Optional[bool] = True
    ) -> Optional[Union[EvalRunRecord, Dict[str, Any]]]:
        """Upsert the name of an eval run in the database, returning raw dictionary.

        Args:
            eval_run_id (str): The ID of the eval run to update.
            name (str): The new name of the eval run.

        Returns:
            Optional[Dict[str, Any]]: The updated eval run, or None if the operation fails.

        Raises:
            Exception: If an error occurs during update.
        """
        try:
            table = await self._get_table(table_type="evals")
            async with self.async_session_factory() as sess, sess.begin():
                stmt = (
                    table.update().where(table.c.run_id == eval_run_id).values(name=name, updated_at=int(time.time()))
                )
                await sess.execute(stmt)

            eval_run_raw = await self.get_eval_run(eval_run_id=eval_run_id, deserialize=deserialize)
            if not eval_run_raw or not deserialize:
                return eval_run_raw

            return EvalRunRecord.model_validate(eval_run_raw)

        except Exception as e:
            log_error(f"Error upserting eval run name {eval_run_id}: {e}")
            return None

    # -- Migrations --

    async def migrate_table_from_v1_to_v2(self, v1_db_schema: str, v1_table_name: str, v1_table_type: str):
        """Migrate all content in the given table to the right v2 table"""

        from agno.db.migrations.v1_to_v2 import (
            get_all_table_content,
            parse_agent_sessions,
            parse_memories,
            parse_team_sessions,
            parse_workflow_sessions,
        )

        # Get all content from the old table
        old_content: list[dict[str, Any]] = get_all_table_content(
            db=self,
            db_schema=v1_db_schema,
            table_name=v1_table_name,
        )
        if not old_content:
            log_info(f"No content to migrate from table {v1_table_name}")
            return

        # Parse the content into the new format
        memories: List[UserMemory] = []
        sessions: Sequence[Union[AgentSession, TeamSession, WorkflowSession]] = []
        if v1_table_type == "agent_sessions":
            sessions = parse_agent_sessions(old_content)
        elif v1_table_type == "team_sessions":
            sessions = parse_team_sessions(old_content)
        elif v1_table_type == "workflow_sessions":
            sessions = parse_workflow_sessions(old_content)
        elif v1_table_type == "memories":
            memories = parse_memories(old_content)
        else:
            raise ValueError(f"Invalid table type: {v1_table_type}")

        # Insert the new content into the new table
        if v1_table_type == "agent_sessions":
            for session in sessions:
                await self.upsert_session(session)
            log_info(f"Migrated {len(sessions)} Agent sessions to table: {self.session_table}")

        elif v1_table_type == "team_sessions":
            for session in sessions:
                await self.upsert_session(session)
            log_info(f"Migrated {len(sessions)} Team sessions to table: {self.session_table}")

        elif v1_table_type == "workflow_sessions":
            for session in sessions:
                await self.upsert_session(session)
            log_info(f"Migrated {len(sessions)} Workflow sessions to table: {self.session_table}")

        elif v1_table_type == "memories":
            for memory in memories:
                await self.upsert_user_memory(memory)
            log_info(f"Migrated {len(memories)} memories to table: {self.memory_table}")
