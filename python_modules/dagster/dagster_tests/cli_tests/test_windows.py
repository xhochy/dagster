import pytest

from dagster.utils import IS_WINDOWS


def test_windows_fail():
    assert not IS_WINDOWS


@pytest.mark.skipif(not IS_WINDOWS, reason='temp windows test')
def test_windows_succeed():
    assert IS_WINDOWS
