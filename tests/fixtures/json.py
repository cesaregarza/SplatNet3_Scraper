import pytest


@pytest.fixture
def json_small() -> dict[str, int]:
    return {
        "a": 1,
        "b": 2,
        "c": 3,
    }


@pytest.fixture
def json_small_linear() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c"), [1, 2, 3]


@pytest.fixture
def json_nested() -> dict[str, int | dict[str, int]]:
    return {
        "a": 1,
        "b": 2,
        "c": {
            "d": 3,
            "e": 4,
        },
    }


@pytest.fixture
def json_nested_linear() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c.d", "c.e"), [1, 2, 3, 4]


@pytest.fixture
def json_list() -> dict[str, int | list[int]]:
    return {
        "a": 1,
        "b": 2,
        "c": [3, 4, 5],
    }


@pytest.fixture
def json_list_linear() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c;0", "c;1", "c;2"), [1, 2, 3, 4, 5]


@pytest.fixture
def json_nested_list() -> dict[str, int | list[dict[str, int]]]:
    return {
        "a": 1,
        "b": 2,
        "c": [
            {
                "d": 3,
                "e": 4,
            },
            {
                "d": 5,
                "e": 6,
            },
        ],
    }


@pytest.fixture
def json_nested_list_linear() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c;0.d", "c;0.e", "c;1.d", "c;1.e"), [1, 2, 3, 4, 5, 6]


@pytest.fixture
def json_deep_nested() -> dict[str, int | dict[str, int | dict[str, int]]]:
    return {
        "a": 1,
        "b": 2,
        "c": {
            "d": 3,
            "e": {
                "f": 4,
                "g": {
                    "h": 5,
                    "i": 6,
                },
            },
        },
    }


@pytest.fixture
def json_deep_nested_linear() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c.d", "c.e.f", "c.e.g.h", "c.e.g.i"), [1, 2, 3, 4, 5, 6]


@pytest.fixture
def json_deep_nested_list() -> dict[
    str, int | list[dict[str, int | dict[str, int]]]
]:
    return {
        "a": 1,
        "b": 2,
        "c": [
            {
                "d": 3,
                "e": {
                    "f": 4,
                    "g": {
                        "h": 5,
                        "i": 6,
                    },
                },
            },
            {
                "d": 7,
                "e": {
                    "f": 8,
                    "g": {
                        "h": 9,
                        "i": 10,
                    },
                },
            },
        ],
    }


@pytest.fixture
def json_deep_nested_list_linear() -> tuple[tuple[str, ...], list[int]]:
    return (
        "a",
        "b",
        "c;0.d",
        "c;0.e.f",
        "c;0.e.g.h",
        "c;0.e.g.i",
        "c;1.d",
        "c;1.e.f",
        "c;1.e.g.h",
        "c;1.e.g.i",
    ), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@pytest.fixture
def json_with_none() -> dict[str, int | list[dict[str, int] | None]]:
    return {
        "a": 1,
        "b": 2,
        "c": [
            None,
            {
                "d": 3,
                "e": 4,
            },
        ],
    }


@pytest.fixture
def json_with_none_linear() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c;0", "c;1.d", "c;1.e"), [1, 2, None, 3, 4]


@pytest.fixture
def json_linear_inserted_none() -> tuple[tuple[str, ...], list[int]]:
    return ("a", "b", "c", "c;0", "c;1.d", "c;1.e"), [1, 2, None, None, 3, 4]
