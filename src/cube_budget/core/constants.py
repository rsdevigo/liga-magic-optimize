"""Card condition ordering (best to worst)."""

CONDITION_ORDER = ["NM", "SP", "MP", "HP", "DMG"]

CONDITION_RANK = {c: i for i, c in enumerate(CONDITION_ORDER)}

LANGUAGES = ["PT", "EN", "ES", "JP", "FR", "DE", "IT", "KO", "RU", "ZH"]

SOLVER_AUTO = "auto"
SOLVER_GREEDY = "greedy"
SOLVER_ILP = "ilp"
SOLVER_ORTOOLS = "ortools"

OBJECTIVE_STORES = "stores"
OBJECTIVE_PRICE = "price"

CACHE_STATUS_OK = "ok"
CACHE_STATUS_ERROR = "error"
CACHE_STATUS_PARTIAL = "partial"
CACHE_STATUS_NOT_FOUND = "not_found"

RUN_STATUS_PENDING = "pending"
RUN_STATUS_RUNNING = "running"
RUN_STATUS_DONE = "done"
RUN_STATUS_FAILED = "failed"

SCHEMA_VERSION = 1
