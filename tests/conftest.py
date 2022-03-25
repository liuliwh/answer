from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def root_dir():
    """Return root dir of tests pytest"""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def data_dir(root_dir):
    return Path(root_dir / "data")


# def pytest_generate_tests(metafunc):
#     if "query" in metafunc.fixturenames:
#         metafunc.parametrize("query", [])
