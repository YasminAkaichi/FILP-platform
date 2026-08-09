from database.connection import DATABASE_PATH
from database.schema import initialize_database


def main() -> None:
    initialize_database()

    print("FILP database initialized successfully.")
    print(f"Database path: {DATABASE_PATH}")


if __name__ == "__main__":
    main()