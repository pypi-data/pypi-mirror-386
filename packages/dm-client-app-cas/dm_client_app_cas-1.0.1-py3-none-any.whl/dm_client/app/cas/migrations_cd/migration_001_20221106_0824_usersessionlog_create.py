from dm_core.migrationcd.abc import AbstractMigrationCD


class MigrationCD(AbstractMigrationCD):

    def __init__(self):
        super().__init__()

    def up(self) -> None:
        query = """
            CREATE TABLE IF NOT EXISTS {}.user_session_log
            (
                id     text,
                auth_type text,
                user_id      text,
                ip_address    text,
                event     text,
                event_at     timestamp,
                primary key (id, event, event_at)
            )
            WITH clustering ORDER BY (event ASC, event_at DESC);
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)

    def down(self) -> None:
        query = """
            DROP TABLE IF EXISTS {}.user_session_log
        """.format(self._keyspace)
        cursor = self._connection.cursor()
        cursor.execute(query)
