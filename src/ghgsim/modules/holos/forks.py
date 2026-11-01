"""Holos Route A fork registry (source-correct default, holos_as_coded options)."""

from functools import lru_cache
from pathlib import Path

from ghgsim.services.forks import Fork, ForkRegistry

_FORKS_JSON = Path(__file__).resolve().parents[3].parent / "data" / "holos_forks_AN_v1.json"


@lru_cache(maxsize=1)
def get_holos_fork_registry() -> ForkRegistry:
    """Load the Holos Phase 2 fork registry from data/holos_forks_AN_v1.json."""
    registry = ForkRegistry()
    registry.load_from_json(_FORKS_JSON)
    return registry


def list_holos_as_coded_forks() -> list[Fork]:
    """Return forks whose non-default option is labelled holos_as_coded."""
    return [
        fork
        for fork in get_holos_fork_registry().list_forks(sort_by="id")
        if fork.label == "holos_as_coded"
    ]


def resolve_option(fork_id: str, fork_settings: dict[str, str] | None = None) -> str:
    """
    Resolve the active option for a registered Holos fork.

    Unknown fork_ids raise; unknown options raise. Missing settings use the
    registered default (source-correct for confirmed bugs).
    """
    registry = get_holos_fork_registry()
    fork = registry.get(fork_id)
    option = (fork_settings or {}).get(fork_id, fork.default)
    if option not in fork.options:
        raise ValueError(f"Invalid option '{option}' for fork '{fork_id}'")
    return option
