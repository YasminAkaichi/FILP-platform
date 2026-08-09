from dataclasses import dataclass


@dataclass
class ServerResult:
    solution: str | None
    solution_found: bool

    total_time: float
    startup_time: float
    learning_time: float
    
    popper_time: float
    federation_time: float
    federation_ratio: float

    number_of_rounds: int
    number_of_programs: int

    final_score: float

    tp: int
    fn: int
    tn: int
    fp: int


@dataclass
class ClientResult:
    client_id: int
    dataset_partition: str

    number_of_examples: int
    number_of_positive_examples: int
    number_of_negative_examples: int

    number_of_evaluations: int

    total_eval_wall: float
    total_eval_cpu: float

    average_eval_wall: float
    average_eval_cpu: float

    final_epsilon_positive: str
    final_epsilon_negative: str

    accepted_solution: bool

    final_score: float

    tp: int
    fn: int
    tn: int
    fp: int