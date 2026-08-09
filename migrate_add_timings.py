from database.connection import get_connection


def column_exists(
    connection,
    table_name: str,
    column_name: str,
) -> bool:
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(
        row["name"] == column_name
        for row in rows
    )


with get_connection() as connection:
    if not column_exists(
        connection,
        "server_results",
        "startup_time_seconds",
    ):
        connection.execute(
            """
            ALTER TABLE server_results
            ADD COLUMN startup_time_seconds
            REAL NOT NULL DEFAULT 0.0
            """
        )
        print("Added startup_time_seconds.")
    else:
        print("startup_time_seconds already exists.")

    if not column_exists(
        connection,
        "server_results",
        "learning_time_seconds",
    ):
        connection.execute(
            """
            ALTER TABLE server_results
            ADD COLUMN learning_time_seconds
            REAL NOT NULL DEFAULT 0.0
            """
        )
        print("Added learning_time_seconds.")
    else:
        print("learning_time_seconds already exists.")

    connection.commit()

print("Migration completed.")