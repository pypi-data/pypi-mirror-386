from dm_core.migrationcd.abc import AbstractMigrationCD


class MigrationCD(AbstractMigrationCD):

    def up(self) -> None:
        query = """
            create table if not exists {}.dm_app_audit_event_log
            (
                id          text primary key,
                application text,
                created_at  timestamp,
                data        blob,
                event_type  text,
                resource_id text
            );
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)

    def down(self) -> None:
        query = """
            DROP TABLE if exists {}.dm_app_audit_event_log
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)
