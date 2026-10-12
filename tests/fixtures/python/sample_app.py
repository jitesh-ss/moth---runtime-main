"""Frozen Python compiler fixture; this module is never imported by the lab."""

from collections import defaultdict


def traced(function):
    return function


class BaseService:
    def identify(self) -> str:
        return "base"


class GreetingService(BaseService):
    @traced
    def greet(self, name: str) -> str:
        return format_name(name)


def format_name(name: str) -> str:
    values = defaultdict(list)
    values["name"].append(name)
    return f"hello {values['name'][0]}"


def test_greeting() -> None:
    assert GreetingService().greet("moth") == "hello moth"

