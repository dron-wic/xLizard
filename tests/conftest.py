# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

FIXTURES_C = Path(__file__).parent / "fixtures" / "c"


@pytest.fixture(scope="session")
def fixtures_c():
    return FIXTURES_C


@pytest.fixture(scope="session")
def all_metrics_c(fixtures_c):
    return fixtures_c / "all_metrics.c"


@pytest.fixture(scope="session")
def file_metrics_c(fixtures_c):
    return fixtures_c / "file_metrics.c"


@pytest.fixture(scope="session")
def large_suite_dir(fixtures_c):
    return fixtures_c / "large"
