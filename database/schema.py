from database.connection import get_connection


SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,

    approach TEXT NOT NULL,
    dataset TEXT NOT NULL,
    number_of_clients INTEGER NOT NULL,
    partition_strategy TEXT NOT NULL,
    learner TEXT NOT NULL,
    random_seed INTEGER NOT NULL,
    rounds INTEGER NOT NULL,
    timeout REAL,
    server_address TEXT NOT NULL,

    status TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS server_results (
    experiment_id INTEGER PRIMARY KEY,

    solution TEXT,
    solution_found INTEGER,
    all_clients_accepted INTEGER,

    total_time_seconds REAL,
    startup_time_seconds REAL NOT NULL DEFAULT 0.0,
    learning_time_seconds REAL NOT NULL DEFAULT 0.0,
    popper_time_seconds REAL,
    federation_time_seconds REAL,
    federation_ratio REAL,

    number_of_rounds INTEGER,
    number_of_programs INTEGER,
    final_score REAL,

    tp INTEGER,
    fn INTEGER,
    tn INTEGER,
    fp INTEGER,

    FOREIGN KEY (experiment_id)
        REFERENCES experiments(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS client_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    experiment_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    dataset_partition TEXT NOT NULL,

    number_of_examples INTEGER,
    number_of_positive_examples INTEGER,
    number_of_negative_examples INTEGER,
    number_of_evaluations INTEGER,

    total_eval_wall_seconds REAL,
    total_eval_cpu_seconds REAL,
    average_eval_wall_seconds REAL,
    average_eval_cpu_seconds REAL,

    -- Flower's federated-evaluation phase (configure_evaluate /
    -- client.evaluate()) runs tester.test() a SECOND time on the same
    -- rules, separately from the fit() phase above. That call was
    -- never timed before, so its cost was silently buried inside
    -- "federation overhead". These columns make it explicit.
    total_evaluate_phase_wall_seconds REAL,
    total_evaluate_phase_cpu_seconds REAL,

    final_epsilon_positive TEXT,
    final_epsilon_negative TEXT,
    accepted_solution INTEGER,
    final_score REAL,

    tp INTEGER,
    fn INTEGER,
    tn INTEGER,
    fp INTEGER,

    UNIQUE (experiment_id, client_id),

    FOREIGN KEY (experiment_id)
        REFERENCES experiments(id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS consensus_results (
    experiment_id INTEGER PRIMARY KEY,

    learner TEXT NOT NULL,
    number_of_clients INTEGER NOT NULL,
    number_of_hypotheses INTEGER NOT NULL,

    hypotheses TEXT NOT NULL,

    tp INTEGER,
    fn INTEGER,
    tn INTEGER,
    fp INTEGER,

    accuracy REAL,
    precision REAL,
    recall REAL,
    f1 REAL,

    FOREIGN KEY (experiment_id)
        REFERENCES experiments(id)
        ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,

    approach TEXT NOT NULL,
    dataset TEXT NOT NULL,
    number_of_clients INTEGER NOT NULL,
    partition_strategy TEXT NOT NULL,

    number_of_runs INTEGER NOT NULL,
    base_seed INTEGER NOT NULL,
    learner TEXT NOT NULL,
    rounds INTEGER NOT NULL,
    timeout REAL,
    server_address TEXT NOT NULL,

    status TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS hypothesis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    experiment_id INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,

    hypothesis TEXT NOT NULL,
    score REAL,
    epsilon_positive TEXT,
    epsilon_negative TEXT,
    is_final_validation INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (experiment_id)
        REFERENCES experiments(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    benchmark_id INTEGER NOT NULL,
    experiment_id INTEGER NOT NULL,
    run_number INTEGER NOT NULL,
    random_seed INTEGER NOT NULL,

    UNIQUE (benchmark_id, run_number),
    UNIQUE (experiment_id),

    FOREIGN KEY (benchmark_id)
        REFERENCES benchmarks(id)
        ON DELETE CASCADE,

    FOREIGN KEY (experiment_id)
        REFERENCES experiments(id)
        ON DELETE CASCADE
);
"""


def _migrate_existing_tables(connection) -> None:
    """Add columns that were introduced after some databases were
    already created. CREATE TABLE IF NOT EXISTS above only helps for
    brand new databases; existing ones need an explicit ALTER TABLE."""

    per_table_migrations = {
        "client_results": {
            "total_evaluate_phase_wall_seconds": (
                "ALTER TABLE client_results "
                "ADD COLUMN total_evaluate_phase_wall_seconds REAL"
            ),
            "total_evaluate_phase_cpu_seconds": (
                "ALTER TABLE client_results "
                "ADD COLUMN total_evaluate_phase_cpu_seconds REAL"
            ),
        },
        # `rounds` used to be the real stopping condition for every
        # approach (hence the old "Max rounds" display everywhere).
        # Collaboration/Coordination now stop on --timeout instead (see
        # FedPopper/srvpopper.py), but that value was never persisted —
        # only passed as a transient CLI arg at launch time — so past
        # runs had no way to show what timeout was actually used.
        "experiments": {
            "timeout": "ALTER TABLE experiments ADD COLUMN timeout REAL",
        },
        "benchmarks": {
            "timeout": "ALTER TABLE benchmarks ADD COLUMN timeout REAL",
        },
    }

    for table_name, migrations in per_table_migrations.items():
        existing_columns = {
            row[1]
            for row in connection.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()
        }

        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(statement)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        _migrate_existing_tables(connection)
        connection.commit()