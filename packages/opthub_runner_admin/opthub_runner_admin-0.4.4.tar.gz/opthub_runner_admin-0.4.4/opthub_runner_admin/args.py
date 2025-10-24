"""This module contains the type of arguments for the CLI."""

from typing import TypedDict


class Args(TypedDict):
    """The type of arguments for the CLI."""

    interval: int
    timeout: int
    num: int
    rm: bool
    mode: str
    dev: bool
    command: list[str]

    evaluator_queue_url: str
    scorer_queue_url: str
    access_key_id: str
    secret_access_key: str
    region_name: str
    table_name: str
