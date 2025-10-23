"""Database-related code."""

import re
from datetime import datetime
from email.utils import format_datetime, parsedate_to_datetime

from psycopg import Connection
from psycopg.sql import SQL, Identifier

# Used to be r"^[a-zA-Z0-9_]+$". But this is more PostgreSQL-compliant.
VALID_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


class Table:
    """Shapefile data table."""

    def __init__(
        self,
        name: str,
        connection: Connection,
        temp_schema: str = "loading",
        data_schema: str = "public",
        metadata_table: str = "external_data",
    ) -> None:
        """
        Work with shapefiles table.

        Args:
            name: name of the table (of a shapefile).
            connection: Database connection object.
            temp_schema: name of temporary schema to create.
            data_schema: name of target schema.
            metadata_table: name of metadata table.

        Raises:
            RuntimeError: if invalid table name provided.
        """

        # Check shapefile name.
        if not VALID_NAME.match(name):
            msg = "Only ASCII alphanumeric table names are supported"
            raise RuntimeError(msg)

        self.name = name
        self.connection = connection
        self.temp_schema = temp_schema
        self.data_schema = data_schema
        self.metadata_table = metadata_table

        # Initialize schema and metadata table -- prepare for import.
        with self.connection.transaction(), self.connection.cursor() as cursor:
            query = SQL("CREATE SCHEMA IF NOT EXISTS {schema}")
            cursor.execute(query.format(schema=Identifier(self.temp_schema)))

            query = SQL("CREATE TABLE IF NOT EXISTS {schema}.{table} (name text primary key, last_modified text)")
            cursor.execute(query.format(schema=Identifier(self.data_schema), table=Identifier(self.metadata_table)))

        # Cleanup temporary table if left from previous import.
        with self.connection.transaction(), self.connection.cursor() as cursor:
            query = SQL("DROP TABLE IF EXISTS {schema}.{table}")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

    @property
    def last_modified(self) -> datetime | None:
        """Read last_modified value from database."""

        with self.connection.transaction(), self.connection.cursor() as cursor:
            query = SQL("SELECT last_modified FROM {schema}.{table} WHERE name = %s")
            query = query.format(schema=Identifier(self.data_schema), table=Identifier(self.metadata_table))
            cursor.execute(query, (self.name,))
            results = cursor.fetchone()

            try:
                return None if results is None else parsedate_to_datetime(results[0])  # pyright: ignore[reportUnknownVariableType]

            # In case of unparsable timestamp.
            except (ValueError, TypeError):
                return None

    def grant_access(self, role: str) -> None:
        """
        Grant read access on temporary table to renderuser.

        Args:
            role: name of user to grant rights.
        """

        with self.connection.transaction(), self.connection.cursor() as cursor:
            query = SQL("GRANT SELECT ON {schema}.{table} TO {role}")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name), role=Identifier(role)))

    def index(self) -> None:
        """Optimize table."""

        with self.connection.transaction(), self.connection.cursor() as cursor:
            # Disable autovacuum while manipulating the table, since it'll get
            # clustered towards the end.
            query = SQL("ALTER TABLE {schema}.{table} SET ( autovacuum_enabled = FALSE )")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

            # ogr creates a ogc_fid column we don't need.
            query = SQL("ALTER TABLE {schema}.{table} DROP COLUMN IF EXISTS ogc_fid")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

            # Null geometries are useless for rendering.
            query = SQL("DELETE FROM {schema}.{table} WHERE way IS NULL")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

            query = SQL("ALTER TABLE {schema}.{table} ALTER COLUMN way SET NOT NULL")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

            # Sorting static tables helps performance and reduces size from the column drop above.
            query = SQL("DROP INDEX IF EXISTS {schema}.{name}")
            query = query.format(schema=Identifier(self.temp_schema), name=Identifier(self.name + "_order"))

            query = SQL("CREATE INDEX {name} ON {schema}.{table} (ST_Envelope(way))")
            query = query.format(name=Identifier(self.name + "_order"), schema=Identifier(self.temp_schema), table=Identifier(self.name))
            cursor.execute(query)

            query = SQL("CLUSTER {schema}.{table} USING {name}")
            query = query.format(name=Identifier(self.name + "_order"), schema=Identifier(self.temp_schema), table=Identifier(self.name))
            cursor.execute(query)

            query = SQL("DROP INDEX {schema}.{name}")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), name=Identifier(self.name + "_order")))

            query = SQL("DROP INDEX IF EXISTS {schema}.{name}")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), name=Identifier(f"{self.name}_way_gist")))

            query = SQL("CREATE INDEX ON {schema}.{table} USING GIST (way) WITH (fillfactor=100)")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

            # Reset autovacuum. The table is static, so this doesn't really
            # matter since it'll never need a vacuum.
            query = SQL("ALTER TABLE {schema}.{table} RESET ( autovacuum_enabled )")
            cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

        # VACUUM can't be run in transaction, so autocommit needs to be turned
        # on.
        old_autocommit = self.connection.autocommit
        try:
            self.connection.autocommit = True
            with self.connection.cursor() as cursor:
                query = SQL("VACUUM ANALYZE {schema}.{table}")
                cursor.execute(query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name)))

        finally:
            self.connection.autocommit = old_autocommit

    def replace(self, last_modified: datetime) -> None:
        """
        Replace data table with temporary one.

        Args:
            last_modified: new value of last_modified column.
        """

        with self.connection.transaction(), self.connection.cursor() as cursor:
            query = SQL("DROP TABLE IF EXISTS {schema}.{table}")
            cursor.execute(query.format(schema=Identifier(self.data_schema), table=Identifier(self.name)))

            query = SQL("ALTER TABLE {schema}.{table} SET SCHEMA {new_schema}")
            query = query.format(schema=Identifier(self.temp_schema), table=Identifier(self.name), new_schema=Identifier(self.data_schema))
            cursor.execute(query)

            # Update metadata table.
            query = SQL("SELECT 1 FROM {schema}.{table} WHERE name = %s")
            query = query.format(schema=Identifier(self.data_schema), table=Identifier(self.metadata_table))
            cursor.execute(query, (self.name,))

            if cursor.rowcount == 0:
                query = SQL("INSERT INTO {schema}.{table} (name, last_modified) VALUES (%s, %s)")
                query = query.format(schema=Identifier(self.data_schema), table=Identifier(self.metadata_table))
                cursor.execute(query, (self.name, format_datetime(last_modified)))

            else:
                query = SQL("UPDATE {schema}.{table} SET last_modified = %s WHERE name = %s")
                query = query.format(schema=Identifier(self.data_schema), table=Identifier(self.metadata_table))
                cursor.execute(query, (format_datetime(last_modified), self.name))
