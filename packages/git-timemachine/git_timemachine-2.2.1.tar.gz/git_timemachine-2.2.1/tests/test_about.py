import importlib

from git_timemachine.__about__ import __version__


def test_version():
    assert __version__ == importlib.metadata.version('git_timemachine')
