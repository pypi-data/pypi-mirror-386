from typing import Set

class MutationErrorConfig:
    success_keywords: Set[str]
    error_prefixes: Set[str]
    error_as_data_prefixes: Set[str]
    error_keywords: Set[str]

    def __init__(
        self,
        success_keywords: Set[str],
        error_prefixes: Set[str],
        error_as_data_prefixes: Set[str],
        error_keywords: Set[str],
    ) -> None: ...
    def is_success(self, status: str) -> bool: ...
    def is_error(self, status: str) -> bool: ...
    def should_return_as_data(self, status: str) -> bool: ...

# Pre-configured error configurations
ALWAYS_DATA_CONFIG: MutationErrorConfig
DEFAULT_ERROR_CONFIG: MutationErrorConfig
STRICT_STATUS_CONFIG: MutationErrorConfig

__all__ = [
    "ALWAYS_DATA_CONFIG",
    "DEFAULT_ERROR_CONFIG",
    "STRICT_STATUS_CONFIG",
    "MutationErrorConfig",
]
