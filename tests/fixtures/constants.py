import pytest


@pytest.fixture
def urand36() -> bytes:
    return (
        b"\xe1\t%\x8c\x15\x7f`\xd9\xc6@\xb59\xea1\n\x93\xdf\x9c\xaa1"
        b"\x17\xaf\x19f|\xe8\xa0l\xce\xef\x9f\xea\xe8\xc3\xfb\xcb"
    )


@pytest.fixture
def urand36_expected() -> bytes:
    return b"4QkljBV_YNnGQLU56jEKk9-cqjEXrxlmfOigbM7vn-row_vL"


@pytest.fixture
def urand32_expected() -> bytes:
    return b"4QkljBV_YNnGQLU56jEKk9-cqjEXrxlmfOigbM7vn-o"
