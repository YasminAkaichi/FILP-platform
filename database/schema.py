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
    server_address TEXT NOT NULL,

    status TEXT NOT NULL,
    error_message TEXT
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


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA)