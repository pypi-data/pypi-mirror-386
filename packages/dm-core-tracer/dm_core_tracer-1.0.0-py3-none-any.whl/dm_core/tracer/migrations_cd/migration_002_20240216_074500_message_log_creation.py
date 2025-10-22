from dm_core.migrationcd.abc import AbstractMigrationCD


class MigrationCD(AbstractMigrationCD):

    def up(self) -> None:
        query = """
            create table if not exists {}.dm_core_tracer_message_log
            (
                message_id   text primary key,
                data         text,
                direction    text,
                exchange_key text,
                request_id   text,
                routing_key  text,
                timestamped  timestamp
            );
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)

    def down(self) -> None:
        query = """
            DROP TABLE if exists {}.dm_core_tracer_message_log
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)
