from dm_core.migrationcd.abc import AbstractMigrationCD


class MigrationCD(AbstractMigrationCD):

    def up(self) -> None:
        query = """
            create table if not exists {}.dm_core_tracer_http_log
            (
                span_id    text primary key,
                body       text,
                created_at timestamp,
                headers    text,
                trace_id   text,
                url_path   text
            );
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)

    def down(self) -> None:
        query = """
            DROP TABLE if exists {}.dm_core_tracer_http_log
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)
